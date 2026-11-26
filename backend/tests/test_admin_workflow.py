from apps.alerts.models import Alert, AlertStatus, AlertTrigger
from apps.audit.models import AuditAction, AuditLog
from apps.incidents import services
from apps.incidents.models import Incident, IncidentStatus
from tests.helpers import KtiTestCase, make_admin


class AdminAccessTests(KtiTestCase):
    def test_admin_endpoints_need_login(self):
        for method, url in [("get", "/api/admin/incidents"), ("get", "/api/admin/alerts"),
                            ("get", "/api/admin/audit-log"), ("post", "/api/admin/incidents/1/verify")]:
            with self.subTest(url=url):
                self.assertEqual(getattr(self.client, method)(url).status_code, 401)

    def test_ordinary_users_are_refused(self):
        self.client.force_authenticate(make_admin("visitor", staff=False))
        self.assertEqual(self.client.get("/api/admin/incidents").status_code, 403)


class WorkflowTests(KtiTestCase):
    def setUp(self):
        super().setUp()
        self.admin = make_admin()
        self.login(self.admin)
        self.incident = services.submit_report(type="FLOODING", description="Water covers the whole road here.", road=self.r_tb)

    def act(self, action, **body):
        return self.client.post(f"/api/admin/incidents/{self.incident.id}/{action}", body, format="json")

    def test_queue_lists_incidents_with_private_details_and_counts(self):
        body = self.client.get("/api/admin/incidents").json()
        self.assertEqual(body["counts"]["SUBMITTED"], 1)
        self.assertEqual(body["results"][0]["reference"], self.incident.reference)
        self.assertIn("reporter_contact", body["results"][0])
        self.assertEqual(self.client.get("/api/admin/incidents?status=VERIFIED").json()["results"], [])

    def test_full_lifecycle_review_verify_resolve(self):
        self.assertEqual(self.act("review").json()["status"], "UNDER_REVIEW")
        verified = self.act("verify").json()
        self.assertEqual(verified["status"], "VERIFIED")
        self.assertEqual(verified["reviewed_by_name"], "Admin One")
        self.assertIsNotNone(verified["verified_at"])
        # now public, and an alert was created automatically
        self.assertEqual(len(self.client.get("/api/incidents").json()), 1)
        alert = Alert.objects.get()
        self.assertEqual((alert.trigger_type, alert.status), (AlertTrigger.INCIDENT_VERIFIED, AlertStatus.ACTIVE))
        self.assertEqual(len(self.client.get("/api/alerts").json()), 1)
        # resolving removes the incident and withdraws its alert
        self.assertEqual(self.act("resolve").json()["status"], "RESOLVED")
        self.assertEqual(self.client.get("/api/incidents").json(), [])
        self.assertEqual(self.client.get("/api/alerts").json(), [])
        actions = list(AuditLog.objects.order_by("id").values_list("action", flat=True))
        self.assertEqual(actions, [AuditAction.REVIEW_INCIDENT, AuditAction.VERIFY_INCIDENT, AuditAction.UPDATE_INCIDENT_STATUS])
        self.assertTrue(all(e.admin == self.admin for e in AuditLog.objects.all()))

    def test_reject_requires_a_reason(self):
        self.assertEqual(self.act("reject").status_code, 400)
        self.assertEqual(self.act("reject", reason="   ").status_code, 400)
        self.incident.refresh_from_db()
        self.assertEqual(self.incident.status, IncidentStatus.SUBMITTED)
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_reject_from_submitted_and_from_under_review(self):
        rejected = self.act("reject", reason="Could not be confirmed").json()
        self.assertEqual((rejected["status"], rejected["rejection_reason"]), ("REJECTED", "Could not be confirmed"))
        other = services.submit_report(type="CRASH", description="Another report to be rejected later.", road=self.r_ab)
        services.start_review(other, self.admin)
        services.reject(other, self.admin, "Duplicate")
        entry = AuditLog.objects.filter(action=AuditAction.REJECT_INCIDENT).first()
        self.assertIn("Rejected", entry.details)
        self.assertEqual(self.client.get("/api/incidents").json(), [])  # rejected is never public

    def test_not_allowed_transitions_give_409(self):
        for action in ("verify", "resolve"):
            with self.subTest(action=action):
                response = self.act(action)
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json()["code"], "invalid_transition")
        self.assertEqual(AuditLog.objects.count(), 0)
        self.act("reject", reason="no")
        self.assertEqual(self.act("review").status_code, 409)  # rejected is final

    def test_unknown_action_and_unknown_incident(self):
        self.assertEqual(self.act("explode").status_code, 404)
        self.assertEqual(self.client.post("/api/admin/incidents/9999/review").status_code, 404)

    def test_audit_log_endpoint(self):
        self.act("review")
        self.act("verify")
        body = self.client.get("/api/admin/audit-log").json()
        self.assertEqual(body["count"], 2)
        self.assertEqual(body["results"][0]["action"], AuditAction.VERIFY_INCIDENT)  # newest first
        self.assertEqual(body["results"][0]["admin_name"], "Admin One")
        self.assertEqual(self.client.get("/api/admin/audit-log?page=99&page_size=1").json()["page"], 2)
