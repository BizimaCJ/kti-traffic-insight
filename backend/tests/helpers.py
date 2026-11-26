from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.network.models import Intersection, Road
from apps.network.services import seed_network
from apps.traffic.levels import classify_delay
from apps.traffic.models import TrafficCondition

PASSWORD = "Kigali-Traffic-2026"


def make_admin(username="admin", staff=True):
    User = get_user_model()
    user = User.objects.create_user(username=username, password=PASSWORD, first_name="Admin", last_name="One")
    user.is_staff = staff
    user.save()
    return user


def make_condition(road, delay, minutes_ago=0, when=None):
    when = when or timezone.now() - timedelta(minutes=minutes_ago)
    return TrafficCondition.objects.create(
        road=road, level=classify_delay(delay), delay_minutes=delay, average_speed_kmh=20.0,
        recorded_at=when, is_simulated=True,
    )


class KtiTestCase(TestCase):
    """Seeds the Nyabugogo network and gives handy shortcuts."""

    def setUp(self):
        cache.clear()  # throttles use the cache
        seed_network()
        self.terminal = Intersection.objects.get(name="Nyabugogo Terminal")
        self.kinamba = Intersection.objects.get(name="Nyabugogo-Kinamba")
        self.muhima = Intersection.objects.get(name="Nyabugogo-Muhima")
        self.r_ta = Road.objects.get(name="Terminal to Nyabugogo-Kinamba")
        self.r_ab = Road.objects.get(name="Nyabugogo-Kinamba to Nyabugogo-Muhima")
        self.r_tb = Road.objects.get(name="Terminal to Nyabugogo-Muhima")
        self.client = APIClient()

    def login(self, user=None):
        self.client.force_authenticate(user or make_admin())

    def report_payload(self, **overrides):
        data = {"type": "CRASH", "road": self.r_tb.id,
                "description": "Two minibuses collided near the bus park entrance."}
        data.update(overrides)
        return data
