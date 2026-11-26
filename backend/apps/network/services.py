"""Road network rules and seed data for the Nyabugogo prototype area."""
from apps.network.models import Intersection, Road

# The two intersections near Nyabugogo Terminal. Latitude/longitude can be added in the Django
# admin (/django-admin/).
SEED_INTERSECTIONS = [
    # name, type, map_x, map_y
    ("Nyabugogo Terminal", Intersection.NodeType.TERMINAL, 14, 66),
    ("Nyabugogo-Kinamba", Intersection.NodeType.JUNCTION, 52, 20),
    ("Nyabugogo-Muhima", Intersection.NodeType.JUNCTION, 86, 66),
]
SEED_ROADS = [
    # name, length km, start, end
    ("Terminal to Nyabugogo-Kinamba", 0.8, "Nyabugogo Terminal", "Nyabugogo-Kinamba"),
    ("Nyabugogo-Kinamba to Nyabugogo-Muhima", 0.7, "Nyabugogo-Kinamba", "Nyabugogo-Muhima"),
    ("Terminal to Nyabugogo-Muhima", 0.9, "Nyabugogo Terminal", "Nyabugogo-Muhima"),
]


def seed_network() -> dict:
    """Create the prototype network. Existing rows are kept as they are."""
    created = {"intersections": 0, "roads": 0}
    for name, node_type, x, y in SEED_INTERSECTIONS:
        _, was_created = Intersection.objects.get_or_create(
            name=name, defaults={"node_type": node_type, "map_x": x, "map_y": y}
        )
        created["intersections"] += was_created
    for name, length, start, end in SEED_ROADS:
        _, was_created = Road.objects.get_or_create(
            name=name,
            defaults={
                "length_km": length,
                "start_intersection": Intersection.objects.get(name=start),
                "end_intersection": Intersection.objects.get(name=end),
            },
        )
        created["roads"] += was_created
    return created
