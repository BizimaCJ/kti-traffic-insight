from datetime import timedelta
from typing import Dict, List, Optional

from django.db.models import Avg, Count, Max, OuterRef, Subquery
from django.db.models.functions import TruncHour
from django.utils import timezone

from apps.network.models import Road
from apps.traffic.models import TrafficCondition

RANGES = {"24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30)}


def latest_conditions() -> List[TrafficCondition]:
    """The most recent reading for every road that has one."""
    newest = TrafficCondition.objects.filter(road=OuterRef("pk")).order_by("-recorded_at", "-id").values("id")[:1]
    ids = [rid for rid in Road.objects.annotate(latest_id=Subquery(newest)).values_list("latest_id", flat=True) if rid]
    return list(TrafficCondition.objects.filter(id__in=ids).select_related("road").order_by("road_id"))


def latest_by_road() -> Dict[int, TrafficCondition]:
    return {c.road_id: c for c in latest_conditions()}


def history(road_id: Optional[int], range_key: str, now=None) -> dict:
    """Hourly averages and the most recent readings for one road (or all roads) - FR 10."""
    now = now or timezone.now()
    since = now - RANGES[range_key]
    readings = TrafficCondition.objects.filter(recorded_at__gte=since)
    if road_id:
        readings = readings.filter(road_id=road_id)
    hourly = (
        readings.annotate(hour=TruncHour("recorded_at"))
        .values("hour")
        .annotate(avg_delay=Avg("delay_minutes"), max_delay=Max("delay_minutes"), avg_speed=Avg("average_speed_kmh"), n=Count("id"))
        .order_by("hour")
    )
    points = [
        {
            "time": row["hour"],
            "avg_delay": round(row["avg_delay"], 1),
            "max_delay": row["max_delay"],
            "avg_speed_kmh": round(row["avg_speed"], 1),
        }
        for row in hourly
    ]
    recent = list(readings.select_related("road")[:30])
    return {"points": points, "recent": recent, "count": readings.count()}
