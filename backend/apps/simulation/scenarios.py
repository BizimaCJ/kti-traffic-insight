"""Simulation scenarios (FR 21): Normal, Peak hour, Incident and Flooding."""
import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

from apps.incidents.models import IncidentType


class Scenario(str, enum.Enum):
    NORMAL = "NORMAL"
    PEAK_HOUR = "PEAK_HOUR"
    INCIDENT = "INCIDENT"
    FLOODING = "FLOODING"

    @classmethod
    def parse(cls, value: str) -> Optional["Scenario"]:
        """Return a Scenario, or None for 'auto' (choose by time of day)."""
        text = value.strip().upper().replace("-", "_").replace(" ", "_")
        if text == "AUTO":
            return None
        try:
            return cls(text)
        except ValueError:
            valid = ", ".join(["auto"] + [s.value.lower() for s in cls])
            raise ValueError(f"Unknown scenario '{value}'. Choose one of: {valid}")


@dataclass(frozen=True)
class ScenarioProfile:
    base_delay: Tuple[int, int]        # delay range (minutes) for every road
    affected_count: Tuple[int, int]    # how many roads get the worse delay
    affected_delay: Tuple[int, int]    # delay range (minutes) for the affected roads
    incident_types: Tuple[str, ...] = ()   # empty = this scenario creates no incident


PROFILES = {
    Scenario.NORMAL: ScenarioProfile((0, 3), (0, 0), (0, 0)),
    Scenario.PEAK_HOUR: ScenarioProfile((3, 9), (1, 1), (9, 15)),
    Scenario.INCIDENT: ScenarioProfile(
        (2, 8), (1, 1), (12, 18),
        (IncidentType.CRASH, IncidentType.BLOCKAGE, IncidentType.ROADWORKS),
    ),
    Scenario.FLOODING: ScenarioProfile((4, 10), (1, 2), (16, 30), (IncidentType.FLOODING,)),
}

# Local rush hours (minutes after midnight): 06:30-09:30 and 16:30-19:30
_PEAK_WINDOWS = ((390, 570), (990, 1170))


def is_peak_hour(local_time: datetime) -> bool:
    minutes = local_time.hour * 60 + local_time.minute
    return any(start <= minutes <= end for start, end in _PEAK_WINDOWS)


def pick_auto_scenario(local_time: datetime, rng) -> Scenario:
    """Choose a scenario from the local time, with a small chance of an incident or flooding."""
    roll = rng.random()
    if roll < 0.01:
        return Scenario.FLOODING
    if roll < 0.05:
        return Scenario.INCIDENT
    return Scenario.PEAK_HOUR if is_peak_hour(local_time) else Scenario.NORMAL
