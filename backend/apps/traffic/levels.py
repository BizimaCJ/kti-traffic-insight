"""Traffic level rules (SRS section 4.3.2). Pure functions, easy to test."""
from typing import Iterable, Optional

from django.conf import settings

from apps.traffic.models import TrafficLevel

SEVERITY = {
    TrafficLevel.FREE_FLOW: 0,
    TrafficLevel.MODERATE: 1,
    TrafficLevel.HEAVY: 2,
    TrafficLevel.BLOCKED: 3,
}


def classify_delay(delay_minutes: int) -> str:
    """Map the extra delay on a road (minutes) to a traffic level."""
    if delay_minutes < 0:
        raise ValueError("delay_minutes cannot be negative")
    if delay_minutes <= settings.FREE_FLOW_MAX_DELAY:
        return TrafficLevel.FREE_FLOW
    if delay_minutes <= settings.MODERATE_MAX_DELAY:
        return TrafficLevel.MODERATE
    if delay_minutes <= settings.HEAVY_MAX_DELAY:
        return TrafficLevel.HEAVY
    return TrafficLevel.BLOCKED


def worst_level(levels: Iterable[str]) -> Optional[str]:
    levels = list(levels)
    return max(levels, key=lambda lv: SEVERITY[lv]) if levels else None
