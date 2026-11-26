from django.test import override_settings

from apps.alerts import services
from apps.alerts.models import Alert, AlertStatus, AlertTrigger
from apps.audit.models import AuditAction, AuditLog
from apps.traffic.services import latest_by_road
from tests.helpers import KtiTestCase, make_admin, make_condition


class ManualAlertTests(KtiTestCase):
    def setUp(self):
        super().setUp()
        self.admin = make_admin()
        self.login(self.admin)

    def test_publish_and_withdraw(self):
        created = self.client.post("/api/admin/alerts", {"message": "Nyabugogo terminal is crowded", "road": self.r_ta.id}, format="json")
        self.assertEqual(created.status_code, 201)
        alert_id = created.json()["id"]
        self.assertEqual(len(self.client.get("/api/alerts").json()), 1)
        withdrawn = self.client.post(f"/api/admin/alerts/{alert_id}/withdraw")
        self.assertEqual(withdrawn.status_code, 200)
        self.assertEqual(withdrawn.json()["status"], "WITHDRAWN")
        self.assertEqual(self.client.get("/api/alerts").json(), [])
        actions = list(AuditLog.objects.order_by("id").values_list("action", flat=True))
        self.assertEqual(actions, [AuditAction.PUBLISH_ALERT, AuditAction.WITHDRAW_ALERT])

    def test_message_is_required_and_road_must_exist(self):
        self.assertEqual(self.client.post("/api/admin/alerts", {"message": "hi"}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/admin/alerts", {"message": "A proper message", "road": 999}, format="json").status_code, 400)
        self.assertEqual(Alert.objects.count(), 0)

    def test_withdrawing_twice_gives_409(self):
        alert = services.publish_manual(self.admin, "Road closed for an event")
        self.client.post(f"/api/admin/alerts/{alert.id}/withdraw")
        self.assertEqual(self.client.post(f"/api/admin/alerts/{alert.id}/withdraw").status_code, 409)

    def test_public_cannot_publish(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post("/api/admin/alerts", {"message": "Fake alert from nobody"}, format="json").status_code, 401)

    def test_admin_list_shows_who_published(self):
        services.publish_manual(self.admin, "Road closed for an event")
        row = self.client.get("/api/admin/alerts").json()["results"][0]
        self.assertEqual((row["published_by_name"], row["trigger_type"]), ("Admin One", "MANUAL"))


class DelayRuleTests(KtiTestCase):
    def feed(self, delay):
        """Save a reading for one road and run the delay rule, like one simulator cycle."""
        previous = latest_by_road()
        condition = make_condition(self.r_tb, delay)
        return services.evaluate_delay_rules([condition], previous)

    def active(self):
        return Alert.objects.filter(trigger_type=AlertTrigger.DELAY_THRESHOLD, status=AlertStatus.ACTIVE)

    def test_alert_when_delay_reaches_threshold(self):
        self.assertEqual(self.feed(4)["created"], 0)
        self.assertEqual(self.feed(10)["created"], 1)  # 10 minutes = threshold
        self.assertEqual(self.active().count(), 1)

    def test_no_duplicate_while_delay_stays_high(self):
        self.feed(4)
        self.feed(12)
        self.assertEqual(self.feed(14)["created"], 0)
        self.assertEqual(self.active().count(), 1)

    def test_alert_clears_when_delay_drops(self):
        self.feed(4)
        self.feed(12)
        self.assertEqual(self.feed(3)["cleared"], 1)
        self.assertEqual(self.active().count(), 0)

    def test_withdrawn_alert_stays_withdrawn_until_delay_rises_again(self):
        self.feed(4)
        self.feed(12)
        services.withdraw(self.active().get(), make_admin())
        self.feed(13)
        self.assertEqual(self.active().count(), 0)       # still congested, admin already withdrew it
        self.feed(3)
        self.assertEqual(self.feed(12)["created"], 1)     # a new rise creates a new alert
        self.assertEqual(self.active().count(), 1)

    @override_settings(ALERT_DELAY_THRESHOLD=5)
    def test_threshold_is_configurable(self):
        self.feed(1)
        self.assertEqual(self.feed(6)["created"], 1)
