import random
from datetime import datetime, timezone

from django.test import SimpleTestCase

from apps.alerts.models import Alert, AlertStatus
from apps.incidents.models import Incident, IncidentStatus, IncidentType
from apps.incidents.services import list_public
from apps.simulation.generator import SimulatedDataGenerator, SimulationError, speed_for_delay
from apps.simulation.scenarios import Scenario, pick_auto_scenario
from apps.traffic.levels import classify_delay
from apps.traffic.models import TrafficLevel
from apps.traffic.services import latest_conditions
from tests.helpers import KtiTestCase

NOW = datetime(2026, 10, 26, 5, 30, tzinfo=timezone.utc)  # 07:30 in Kigali (UTC+2)


def generator(scenario, seed=1, clock=lambda: NOW):
    return SimulatedDataGenerator(scenario, rng=random.Random(seed), clock=clock)


class GeneratorTests(KtiTestCase):
    def test_normal_scenario_is_mostly_free_flow(self):
        result = generator("normal").run_cycle()
        conditions = latest_conditions()
        self.assertEqual((result.conditions_created, len(conditions)), (3, 3))
        self.assertTrue(all(c.delay_minutes <= 3 and c.is_simulated for c in conditions))
        self.assertEqual(result.incidents_created, 0)

    def test_level_always_matches_delay(self):
        for seed in range(15):
            generator("peak_hour", seed).run_cycle()
        for c in latest_conditions():
            self.assertEqual(c.level, classify_delay(c.delay_minutes))

    def test_peak_hour_has_a_heavy_road(self):
        generator("peak_hour").run_cycle()
        self.assertTrue(any(c.level == TrafficLevel.HEAVY for c in latest_conditions()))

    def test_flooding_blocks_a_road_and_creates_verified_flood_incident_with_alert(self):
        result = generator("flooding").run_cycle()
        self.assertTrue(any(c.level == TrafficLevel.BLOCKED for c in latest_conditions()))
        incidents = list(list_public())
        self.assertEqual(result.incidents_created, len(incidents))
        self.assertTrue(incidents and all(i.type == IncidentType.FLOODING and i.is_simulated for i in incidents))
        self.assertTrue(Alert.objects.filter(incident__in=incidents, status=AlertStatus.ACTIVE).count() == len(incidents))

    def test_incidents_and_their_alerts_clear_when_scenario_returns_to_normal(self):
        generator("incident").run_cycle()
        self.assertEqual(len(list_public()), 1)
        result = generator("normal").run_cycle()
        self.assertEqual(result.incidents_resolved, 1)
        self.assertEqual(len(list_public()), 0)
        self.assertEqual(Incident.objects.get().status, IncidentStatus.RESOLVED)
        self.assertFalse(Alert.objects.filter(status=AlertStatus.ACTIVE).exists())

    def test_one_active_simulated_incident_per_road(self):
        for seed in range(25):
            generator("flooding", seed).run_cycle()
        roads = [i.road_id for i in list_public()]
        self.assertEqual(len(roads), len(set(roads)))

    def test_delay_alert_is_raised_and_cleared_by_cycles(self):
        generator("peak_hour").run_cycle()   # one road gets 9-15 minutes
        generator("normal", 2).run_cycle()
        self.assertFalse(Alert.objects.filter(status=AlertStatus.ACTIVE).exists())

    def test_auto_uses_kigali_time_not_utc(self):
        class Quiet(random.Random):
            def random(self):
                return 0.5
        gen = SimulatedDataGenerator("auto", rng=Quiet(1), clock=lambda: NOW)
        self.assertEqual(gen.run_cycle().scenario, Scenario.PEAK_HOUR)


class BackfillTests(KtiTestCase):
    def test_backfill_creates_history_with_a_rush_hour_pattern(self):
        from apps.traffic.models import TrafficCondition
        count = generator("normal").backfill_history(days=2, step_minutes=30)
        self.assertEqual(count, 2 * 48 * 3)                     # 2 days x 48 steps x 3 roads
        self.assertEqual(TrafficCondition.objects.count(), count)
        self.assertFalse(Incident.objects.exists() or Alert.objects.exists())
        from django.db.models import Avg
        from django.db.models.functions import ExtractHour
        by_hour = dict(TrafficCondition.objects.annotate(h=ExtractHour("recorded_at")).values_list("h").annotate(a=Avg("delay_minutes")))
        self.assertGreater(by_hour[7], by_hour[13] + 2)          # 07:00 is rush hour, 13:00 is quiet

    def test_later_journey_uses_the_backfilled_history(self):
        from datetime import timedelta
        from django.utils import timezone
        generator("normal", clock=timezone.now).backfill_history(days=7, step_minutes=10)
        generator("normal", clock=timezone.now).run_cycle()
        later = timezone.now() + timedelta(hours=3)
        body = self.client.post("/api/journeys", {"origin": self.terminal.id, "destination": self.muhima.id,
                                                   "departure_time": later.isoformat()}, format="json").json()
        self.assertEqual(body["departure"]["basis"], "history")


class EmptyNetworkTests(KtiTestCase):
    def test_clear_error_when_network_is_empty(self):
        from apps.network.models import Road
        Road.objects.all().delete()
        with self.assertRaises(SimulationError):
            generator("normal").run_cycle()


class ScenarioTests(SimpleTestCase):
    def test_unknown_scenario_is_rejected(self):
        with self.assertRaises(ValueError):
            SimulatedDataGenerator("bogus")

    def test_set_scenario_accepts_auto_and_names(self):
        gen = SimulatedDataGenerator("flooding")
        self.assertEqual(gen.scenario, Scenario.FLOODING)
        gen.set_scenario("auto")
        self.assertIsNone(gen.scenario)
        gen.set_scenario("Peak-Hour")
        self.assertEqual(gen.scenario, Scenario.PEAK_HOUR)

    def test_auto_scenario_follows_local_time(self):
        class Fixed:
            def __init__(self, v):
                self.v = v

            def random(self):
                return self.v

        at = lambda h, m: datetime(2026, 10, 26, h, m)
        self.assertEqual(pick_auto_scenario(at(7, 30), Fixed(0.5)), Scenario.PEAK_HOUR)
        self.assertEqual(pick_auto_scenario(at(17, 0), Fixed(0.5)), Scenario.PEAK_HOUR)
        self.assertEqual(pick_auto_scenario(at(13, 0), Fixed(0.5)), Scenario.NORMAL)
        self.assertEqual(pick_auto_scenario(at(13, 0), Fixed(0.03)), Scenario.INCIDENT)
        self.assertEqual(pick_auto_scenario(at(13, 0), Fixed(0.005)), Scenario.FLOODING)

    def test_speed_drops_as_delay_grows(self):
        free, slow = speed_for_delay(0.8, 0, 30.0), speed_for_delay(0.8, 9, 30.0)
        self.assertEqual(free, 30.0)
        self.assertTrue(0 < slow < free)
