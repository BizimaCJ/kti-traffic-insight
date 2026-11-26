from datetime import timedelta

from django.utils import timezone

from apps.network.models import Intersection, Road
from tests.helpers import KtiTestCase, make_condition


class JourneyTests(KtiTestCase):
    def plan(self, **extra):
        body = {"origin": self.terminal.id, "destination": self.muhima.id}
        body.update(extra)
        return self.client.post("/api/journeys", body, format="json")

    def set_delays(self, ta, ab, tb):
        make_condition(self.r_ta, ta)
        make_condition(self.r_ab, ab)
        make_condition(self.r_tb, tb)

    def test_finds_direct_and_alternative_route(self):
        self.set_delays(2, 1, 4)
        body = self.plan().json()
        names = [r["name"] for r in body["routes"]]
        self.assertEqual(names, ["Direct", "Via Nyabugogo-Kinamba"])
        self.assertTrue(body["routes"][0]["is_main"])
        self.assertEqual(body["routes"][0]["intersections"], ["Nyabugogo Terminal", "Nyabugogo-Muhima"])

    def test_delay_is_summed_along_the_route(self):
        self.set_delays(3, 4, 9)
        direct, via = self.plan().json()["routes"]
        self.assertEqual(direct["delay_minutes"], 9)
        self.assertEqual(via["delay_minutes"], 7)       # 3 + 4
        self.assertEqual(direct["level"], "HEAVY")      # 9 minutes
        self.assertEqual(via["level"], "MODERATE")      # 7 minutes
        self.assertEqual(len(via["segments"]), 2)

    def test_recommends_the_faster_alternative_when_direct_is_slow(self):
        self.set_delays(1, 1, 14)
        body = self.plan().json()
        via = next(r for r in body["routes"] if r["name"] == "Via Nyabugogo-Kinamba")
        self.assertEqual(body["recommended_route_id"], via["id"])
        self.assertTrue(via["is_recommended"])
        self.assertGreater(body["time_saved_minutes"], 5)

    def test_keeps_the_main_route_when_it_is_fastest(self):
        self.set_delays(6, 6, 1)
        body = self.plan().json()
        self.assertEqual(body["recommended_route_id"], body["main_route_id"])
        self.assertEqual(body["time_saved_minutes"], 0)

    def test_delay_is_unknown_when_there_is_no_data(self):
        body = self.plan().json()
        self.assertIsNone(body["routes"][0]["delay_minutes"])
        self.assertIsNone(body["recommended_route_id"])

    def test_same_origin_and_destination_is_rejected(self):
        response = self.plan(destination=self.terminal.id)
        self.assertEqual(response.status_code, 400)
        self.assertIn("destination", response.json())

    def test_unknown_place_is_rejected(self):
        self.assertEqual(self.plan(origin=9999).status_code, 400)

    def test_departure_time_must_be_sensible(self):
        past = (timezone.now() - timedelta(hours=2)).isoformat()
        far = (timezone.now() + timedelta(hours=30)).isoformat()
        self.assertEqual(self.plan(departure_time=past).status_code, 400)
        self.assertEqual(self.plan(departure_time=far).status_code, 400)

    def test_later_departure_uses_history_for_that_hour(self):
        self.set_delays(0, 0, 2)
        later = timezone.now() + timedelta(hours=2)
        for day in range(1, 8):  # the same hour on seven earlier days: delay 12 on the direct road
            make_condition(self.r_tb, 12, when=later - timedelta(days=day))
            make_condition(self.r_ta, 1, when=later - timedelta(days=day))
            make_condition(self.r_ab, 1, when=later - timedelta(days=day))
        body = self.plan(departure_time=later.isoformat()).json()
        self.assertEqual(body["departure"]["basis"], "history")
        self.assertFalse(body["departure"]["is_now"])
        self.assertEqual(body["routes"][0]["delay_minutes"], 12)

    def test_later_departure_falls_back_to_current_without_history(self):
        self.set_delays(0, 0, 5)
        later = timezone.now() + timedelta(hours=2)
        body = self.plan(departure_time=later.isoformat()).json()
        self.assertEqual(body["departure"]["basis"], "current")
        self.assertEqual(body["routes"][0]["delay_minutes"], 5)

    def test_timeline_has_four_points(self):
        self.set_delays(0, 0, 5)
        timeline = self.plan().json()["timeline"]
        self.assertEqual([p["offset_minutes"] for p in timeline], [0, 30, 60, 90])

    def test_no_alternative_message(self):
        lonely_a = Intersection.objects.create(name="Lonely A")
        lonely_b = Intersection.objects.create(name="Lonely B")
        Road.objects.create(name="Only road", length_km=1, start_intersection=lonely_a, end_intersection=lonely_b)
        body = self.client.post("/api/journeys", {"origin": lonely_a.id, "destination": lonely_b.id}, format="json").json()
        self.assertEqual(len(body["routes"]), 1)
        self.assertIn("no alternative", body["message"].lower())

    def test_disconnected_places_give_a_clear_message(self):
        lonely = Intersection.objects.create(name="Island")
        body = self.client.post("/api/journeys", {"origin": lonely.id, "destination": self.terminal.id}, format="json").json()
        self.assertEqual(body["routes"], [])
        self.assertIn("No route", body["message"])
