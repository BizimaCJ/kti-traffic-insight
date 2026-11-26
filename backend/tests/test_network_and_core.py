from unittest import mock

from django.db.utils import OperationalError

from apps.network.models import Intersection, Road
from apps.network.services import seed_network
from tests.helpers import KtiTestCase


class NetworkTests(KtiTestCase):
    def test_seed_is_idempotent(self):
        again = seed_network()
        self.assertEqual(again, {"intersections": 0, "roads": 0})
        self.assertEqual(Intersection.objects.count(), 3)
        self.assertEqual(Road.objects.count(), 3)

    def test_network_endpoint(self):
        body = self.client.get("/api/network").json()
        self.assertEqual(len(body["intersections"]), 3)
        self.assertEqual(len(body["roads"]), 3)
        self.assertIn("map_x", body["intersections"][0])
        self.assertEqual(body["roads"][0]["start_name"], "Nyabugogo Terminal")
        self.assertEqual(body["thresholds"], {"free_flow_max": 2, "moderate_max": 7, "heavy_max": 15, "alert": 10})


class CoreTests(KtiTestCase):
    def test_health(self):
        self.assertEqual(self.client.get("/api/health").json(), {"status": "ok"})

    def test_spa_page_is_served(self):
        response = self.client.get("/journey")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response["Content-Type"])

    def test_database_down_gives_friendly_503(self):
        with mock.patch("apps.overview.views.traffic_services.latest_conditions", side_effect=OperationalError("down")):
            response = self.client.get("/api/overview")
        self.assertEqual(response.status_code, 503)
        self.assertIn("temporarily unavailable", response.json()["detail"])
