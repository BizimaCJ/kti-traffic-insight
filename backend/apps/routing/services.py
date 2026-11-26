"""Journey planning (FR 4, 5, 11): estimated delay and alternative routes between two intersections.

The road network is small, so every simple path between the two intersections is found and
compared. Delay for a road comes from its latest reading; for a departure time later in the day it
comes from the average of past readings at the same hour (when enough history exists).
"""
from datetime import timedelta
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models import Avg, Count
from django.db.models.functions import ExtractHour
from django.utils import timezone

from apps.network.models import Intersection, Road
from apps.traffic.levels import classify_delay
from apps.traffic.models import TrafficCondition
from apps.traffic.services import latest_by_road

MAX_HOPS = 6
HISTORY_DAYS = 14
MIN_SAMPLES = 5
CURRENT_WINDOW = timedelta(minutes=15)
TIMELINE_OFFSETS = (0, 30, 60, 90)


class DelayEstimator:
    """Expected delay (minutes) for a road at a given time, and what the estimate is based on."""

    def __init__(self, now):
        self.now = now
        self.latest = latest_by_road()
        self._history: Dict[int, Dict[int, Tuple[float, int]]] = {}

    def _history_for_hour(self, hour: int) -> Dict[int, Tuple[float, int]]:
        if hour not in self._history:
            rows = (
                TrafficCondition.objects.filter(recorded_at__gte=self.now - timedelta(days=HISTORY_DAYS))
                .annotate(h=ExtractHour("recorded_at")).filter(h=hour)
                .values("road_id").annotate(avg=Avg("delay_minutes"), n=Count("id"))
            )
            self._history[hour] = {r["road_id"]: (r["avg"], r["n"]) for r in rows}
        return self._history[hour]

    def delay(self, road_id: int, when) -> Tuple[Optional[int], str]:
        if when is None or abs(when - self.now) <= CURRENT_WINDOW:
            latest = self.latest.get(road_id)
            return (latest.delay_minutes if latest else None), "current"
        hour = when.astimezone(ZoneInfo(settings.TIME_ZONE)).hour
        avg, n = self._history_for_hour(hour).get(road_id, (None, 0))
        if avg is not None and n >= MIN_SAMPLES:
            return int(round(avg)), "history"
        latest = self.latest.get(road_id)
        return (latest.delay_minutes if latest else None), "current"


def find_paths(origin_id: int, destination_id: int) -> List[Tuple[List[int], List[Road]]]:
    """All simple paths (roads can be driven in both directions)."""
    roads = list(Road.objects.select_related("start_intersection", "end_intersection"))
    adjacency: Dict[int, List[Tuple[int, Road]]] = {}
    for road in roads:
        adjacency.setdefault(road.start_intersection_id, []).append((road.end_intersection_id, road))
        adjacency.setdefault(road.end_intersection_id, []).append((road.start_intersection_id, road))
    found: List[Tuple[List[int], List[Road]]] = []

    def walk(node: int, nodes: List[int], used: List[Road]):
        if node == destination_id:
            found.append((list(nodes), list(used)))
            return
        if len(used) >= MAX_HOPS:
            return
        for neighbour, road in adjacency.get(node, []):
            if neighbour not in nodes:
                nodes.append(neighbour)
                used.append(road)
                walk(neighbour, nodes, used)
                nodes.pop()
                used.pop()

    walk(origin_id, [origin_id], [])
    return found


def _build_route(index: int, nodes: List[int], roads: List[Road], names: Dict[int, str],
                 estimator: DelayEstimator, when) -> dict:
    segments, basis_values, delays = [], set(), []
    for road in roads:
        delay, basis = estimator.delay(road.id, when)
        basis_values.add(basis)
        delays.append(delay)
        segments.append({
            "road_id": road.id, "road_name": road.name, "length_km": road.length_km, "delay_minutes": delay,
            "level": classify_delay(delay) if delay is not None else None,
        })
    distance = round(sum(r.length_km for r in roads), 2)
    free_minutes = round(distance / settings.FREE_FLOW_SPEED_KMH * 60, 1)
    known = all(d is not None for d in delays)
    delay_total = sum(delays) if known else None
    middle = [names[n] for n in nodes[1:-1]]
    return {
        "id": index,
        "name": "Direct" if not middle else "Via " + " and ".join(middle),
        "intersection_ids": nodes,
        "intersections": [names[n] for n in nodes],
        "segments": segments,
        "distance_km": distance,
        "free_flow_minutes": free_minutes,
        "delay_minutes": delay_total,
        "total_minutes": round(free_minutes + delay_total, 1) if known else None,
        "level": classify_delay(delay_total) if known else None,
        "basis": "history" if basis_values == {"history"} else "current",
    }


def plan_journey(origin: Intersection, destination: Intersection, departure_time=None, now=None) -> dict:
    now = now or timezone.now()
    when = departure_time
    names = dict(Intersection.objects.values_list("id", "name"))
    estimator = DelayEstimator(now)
    paths = find_paths(origin.id, destination.id)
    result = {
        "origin": {"id": origin.id, "name": origin.name},
        "destination": {"id": destination.id, "name": destination.name},
        "departure": {
            "time": (when or now).isoformat(),
            "is_now": when is None or abs(when - now) <= CURRENT_WINDOW,
        },
        "simulated": True,
        "routes": [], "main_route_id": None, "recommended_route_id": None,
        "time_saved_minutes": None, "timeline": [], "message": "",
    }
    if not paths:
        result["message"] = "No route was found between these two places in the Nyabugogo area."
        return result

    routes = [_build_route(i, n, r, names, estimator, when) for i, (n, r) in enumerate(paths, start=1)]
    main = min(routes, key=lambda r: (r["distance_km"], len(r["segments"])))
    others = sorted((r for r in routes if r is not main),
                    key=lambda r: (r["total_minutes"] is None, r["total_minutes"] or 0, r["distance_km"]))
    for r in routes:
        r["is_main"] = r is main
    known = [r for r in routes if r["total_minutes"] is not None]
    recommended = min(known, key=lambda r: r["total_minutes"]) if known else None
    for r in routes:
        r["is_recommended"] = recommended is not None and r is recommended

    result["routes"] = [main] + others
    result["main_route_id"] = main["id"]
    result["departure"]["basis"] = main["basis"]
    if recommended and main["total_minutes"] is not None:
        result["recommended_route_id"] = recommended["id"]
        result["time_saved_minutes"] = round(main["total_minutes"] - recommended["total_minutes"], 1)
    if not others:
        result["message"] = "There is no alternative route for this journey."

    base = when or now
    for offset in TIMELINE_OFFSETS:
        at = base + timedelta(minutes=offset)
        point = _build_route(0, paths[routes.index(main)][0], paths[routes.index(main)][1], names, estimator, at)
        result["timeline"].append({
            "offset_minutes": offset, "depart_at": at.isoformat(),
            "delay_minutes": point["delay_minutes"], "basis": point["basis"],
        })
    return result
