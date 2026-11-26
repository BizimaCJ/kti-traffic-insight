from datetime import timedelta

from django.utils import timezone

from tests.helpers import KtiTestCase, make_condition


class HistoryTests(KtiTestCase):
    def setUp(self):
        super().setUp()
        for hours_ago, delay in [(1, 4), (2, 6), (3, 8), (30, 10), (200, 12)]:
            make_condition(self.r_tb, delay, minutes_ago=hours_ago * 60)
        make_condition(self.r_ta, 1, minutes_ago=60)

    def test_ranges_limit_the_data(self):
        counts = {r: self.client.get(f"/api/traffic/history?range={r}").json()["count"] for r in ("24h", "7d", "30d")}
        self.assertEqual(counts, {"24h": 4, "7d": 5, "30d": 6})

    def test_road_filter_and_points(self):
        body = self.client.get(f"/api/traffic/history?road={self.r_tb.id}&range=24h").json()
        self.assertEqual(body["road"]["name"], "Terminal to Nyabugogo-Muhima")
        self.assertEqual(body["count"], 3)
        self.assertEqual(sorted(p["avg_delay"] for p in body["points"]), [4.0, 6.0, 8.0])
        self.assertEqual(len(body["recent"]), 3)

    def test_empty_history_is_not_an_error(self):
        body = self.client.get(f"/api/traffic/history?road={self.r_ab.id}&range=24h").json()
        self.assertEqual((body["count"], body["points"], body["recent"]), (0, [], []))

    def test_bad_parameters(self):
        self.assertEqual(self.client.get("/api/traffic/history?range=1y").status_code, 400)
        self.assertEqual(self.client.get("/api/traffic/history?road=999").status_code, 400)
        self.assertEqual(self.client.get("/api/traffic/history?road=abc").status_code, 400)

    def test_history_is_public(self):
        self.assertEqual(self.client.get("/api/traffic/history").status_code, 200)


class OverviewTests(KtiTestCase):
    def test_empty(self):
        body = self.client.get("/api/overview").json()
        self.assertFalse(body["has_data"])
        self.assertEqual((body["roads"], body["incidents"], body["alerts"]), ([], [], []))
        self.assertIsNone(body["worst_level"])

    def test_latest_reading_per_road_only(self):
        make_condition(self.r_tb, 1, minutes_ago=10)
        make_condition(self.r_tb, 12, minutes_ago=1)
        make_condition(self.r_ta, 3)
        body = self.client.get("/api/overview").json()
        self.assertTrue(body["has_data"] and body["simulated"])
        self.assertEqual(len(body["roads"]), 2)
        tb = next(r for r in body["roads"] if r["road_id"] == self.r_tb.id)
        self.assertEqual((tb["delay_minutes"], tb["level"]), (12, "HEAVY"))
        self.assertEqual(body["worst_level"], "HEAVY")

    def test_conditions_endpoint(self):
        make_condition(self.r_tb, 3)
        self.assertEqual(len(self.client.get("/api/traffic/conditions").json()), 1)
