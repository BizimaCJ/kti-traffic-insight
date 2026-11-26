"""SimulatedDataGenerator (class diagram CD-1, sequence diagram SD-8).

Each cycle it saves one TrafficCondition per road, creates or clears simulated incidents, and
then evaluates the alert rules. Everything it writes is flagged as simulated.
"""
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Callable, List, Optional, Union
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction

from apps.alerts import services as alert_services
from apps.incidents.models import Incident, IncidentStatus, IncidentType
from apps.network.models import Road
from apps.simulation.scenarios import PROFILES, Scenario, is_peak_hour, pick_auto_scenario
from apps.traffic.levels import classify_delay
from apps.traffic.models import TrafficCondition
from apps.traffic.services import latest_by_road

_DESCRIPTIONS = {
    IncidentType.CRASH: "Simulated crash reported on {road}. Expect delays.",
    IncidentType.FLOODING: "Simulated flooding on {road}. Traffic is slow or stopped.",
    IncidentType.ROADWORKS: "Simulated roadworks on {road}. One lane may be closed.",
    IncidentType.BLOCKAGE: "Simulated blockage on {road}. Use another route if you can.",
    IncidentType.OTHER: "Simulated incident on {road}.",
}


class SimulationError(Exception):
    pass


@dataclass
class CycleResult:
    scenario: Scenario
    recorded_at: datetime
    conditions_created: int
    incidents_created: int
    incidents_resolved: int
    alerts_created: int
    alerts_cleared: int


def speed_for_delay(length_km: float, delay_minutes: int, free_flow_speed_kmh: float) -> float:
    """Average speed on a road when the free-flow travel time is stretched by the delay."""
    free_minutes = length_km / free_flow_speed_kmh * 60
    return round(length_km / ((free_minutes + delay_minutes) / 60), 1)


class SimulatedDataGenerator:
    def __init__(
        self,
        scenario: Union[Scenario, str, None] = "auto",
        refresh_interval_seconds: Optional[int] = None,
        rng: Optional[random.Random] = None,
        clock: Optional[Callable[[], datetime]] = None,
    ):
        self.refresh_interval_seconds = refresh_interval_seconds or settings.SIMULATION_INTERVAL_SECONDS
        self.rng = rng or random.Random()
        self.clock = clock or (lambda: datetime.now(dt_timezone.utc))
        self.scenario: Optional[Scenario] = None
        self.set_scenario(scenario)

    def set_scenario(self, scenario: Union[Scenario, str, None]) -> None:
        """Set the scenario, or 'auto' / None to choose by time of day."""
        self.scenario = Scenario.parse(scenario) if isinstance(scenario, str) else scenario

    def _resolve_scenario(self, now: datetime) -> Scenario:
        if self.scenario is not None:
            return self.scenario
        return pick_auto_scenario(now.astimezone(ZoneInfo(settings.TIME_ZONE)), self.rng)

    @transaction.atomic
    def run_cycle(self) -> CycleResult:
        roads = list(Road.objects.all())
        if not roads:
            raise SimulationError("The road network is empty. Run `python manage.py seed` first.")
        now = self.clock()
        scenario = self._resolve_scenario(now)
        profile = PROFILES[scenario]
        count = self.rng.randint(*profile.affected_count)
        affected = self.rng.sample(roads, min(count, len(roads))) if count else []

        previous = latest_by_road()
        conditions = self.generate_traffic_conditions(roads, affected, scenario, now)
        created, resolved = self.generate_incidents(affected, scenario, now)
        alerts = alert_services.evaluate_delay_rules(conditions, previous)
        return CycleResult(scenario, now, len(conditions), created, resolved, alerts["created"], alerts["cleared"])

    def build_conditions(self, roads: List[Road], affected: List[Road], scenario: Scenario, now) -> List[TrafficCondition]:
        """Make (but do not save) one reading per road."""
        profile = PROFILES[scenario]
        affected_ids = {r.id for r in affected}
        conditions = []
        for road in roads:
            low, high = profile.affected_delay if road.id in affected_ids else profile.base_delay
            delay = self.rng.randint(low, high)
            conditions.append(TrafficCondition(
                road=road, level=classify_delay(delay), delay_minutes=delay,
                average_speed_kmh=speed_for_delay(road.length_km, delay, settings.FREE_FLOW_SPEED_KMH),
                recorded_at=now, is_simulated=True,
            ))
        return conditions

    def generate_traffic_conditions(self, roads: List[Road], affected: List[Road], scenario: Scenario, now) -> List[TrafficCondition]:
        return TrafficCondition.objects.bulk_create(self.build_conditions(roads, affected, scenario, now))

    @transaction.atomic
    def backfill_history(self, days: int = 7, step_minutes: int = 10, now: Optional[datetime] = None) -> int:
        """Save past readings that follow the daily rhythm (rush hours 06:30-09:30 and 16:30-19:30).

        Gives the History page and the 'leave later' estimates something to work with. No incidents or alerts.
        """
        roads = list(Road.objects.all())
        if not roads:
            raise SimulationError("The road network is empty. Run `python manage.py seed` first.")
        now = now or self.clock()
        zone = ZoneInfo(settings.TIME_ZONE)
        rows: List[TrafficCondition] = []
        moment = now - timedelta(days=days)
        while moment < now:
            scenario = Scenario.PEAK_HOUR if is_peak_hour(moment.astimezone(zone)) else Scenario.NORMAL
            profile = PROFILES[scenario]
            count = self.rng.randint(*profile.affected_count)
            affected = self.rng.sample(roads, min(count, len(roads))) if count else []
            rows.extend(self.build_conditions(roads, affected, scenario, moment))
            moment += timedelta(minutes=step_minutes)
        TrafficCondition.objects.bulk_create(rows, batch_size=2000)
        return len(rows)

    def generate_incidents(self, affected: List[Road], scenario: Scenario, now):
        """Create simulated incidents for incident scenarios; clear them otherwise. A road never has two."""
        profile = PROFILES[scenario]
        active = Incident.objects.filter(is_simulated=True, status=IncidentStatus.VERIFIED)
        created = resolved = 0
        if not profile.incident_types:
            for incident in active:
                incident.status = IncidentStatus.RESOLVED
                incident.save(update_fields=["status"])
                alert_services.withdraw_for_incident(incident)
                resolved += 1
            return created, resolved
        for road in affected:
            if active.filter(road=road).exists():
                continue
            kind = self.rng.choice(profile.incident_types)
            incident = Incident.objects.create(
                type=kind, description=_DESCRIPTIONS[kind].format(road=road.name), status=IncidentStatus.VERIFIED,
                reported_at=now, verified_at=now, is_simulated=True, road=road,
            )
            alert_services.on_incident_verified(incident)
            created += 1
        return created, resolved
