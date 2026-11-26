from datetime import timedelta

from django.test import override_settings
from django.utils import timezone

from apps.incidents import services
from apps.incidents.models import Incident, IncidentStatus
from tests.helpers import KtiTestCase


class AnonymousReportTests(KtiTestCase):
    def test_report_needs_no_login_and_is_saved_as_submitted(self):
        response = self.client.post("/api/incidents/report", self.report_payload(), format="json")
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body["reference"].startswith("KTI-"))
        self.assertEqual(body["status"], "SUBMITTED")
        incident = Incident.objects.get()
        self.assertEqual(incident.status, IncidentStatus.SUBMITTED)
        self.assertEqual((incident.reporter_name, incident.reporter_contact), ("", ""))

    def test_optional_name_and_contact_are_kept(self):
        self.client.post("/api/incidents/report",
                         self.report_payload(reporter_name="Jean", reporter_contact="0780000000"), format="json")
        incident = Incident.objects.get()
        self.assertEqual((incident.reporter_name, incident.reporter_contact), ("Jean", "0780000000"))

    def test_submitted_report_is_not_public(self):
        self.client.post("/api/incidents/report", self.report_payload(), format="json")
        self.assertEqual(self.client.get("/api/incidents").json(), [])

    def test_validation_errors(self):
        bad = [self.report_payload(description="short"), self.report_payload(road=9999),
               self.report_payload(type="ALIENS"), self.report_payload(description="   ")]
        for payload in bad:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/api/incidents/report", payload, format="json").status_code, 400)
        self.assertEqual(Incident.objects.count(), 0)

    def test_exact_repeat_within_window_is_refused(self):
        self.client.post("/api/incidents/report", self.report_payload(), format="json")
        again = self.client.post("/api/incidents/report", self.report_payload(), format="json")
        self.assertEqual(again.status_code, 409)
        self.assertEqual(again.json()["code"], "duplicate")
        self.assertEqual(Incident.objects.count(), 1)

    def test_repeat_after_window_is_accepted(self):
        now = timezone.now()
        services.submit_report(type="CRASH", description="Minibus crash near the gate.", road=self.r_tb, now=now - timedelta(minutes=30))
        again = services.submit_report(type="CRASH", description="Minibus crash near the gate.", road=self.r_tb, now=now)
        self.assertEqual(Incident.objects.count(), 2)
        self.assertEqual(again.possible_duplicate_of.reference, Incident.objects.order_by("id").first().reference)

    def test_similar_active_report_is_flagged_not_refused(self):
        first = services.submit_report(type="CRASH", description="A truck crashed near the market.", road=self.r_tb)
        second = services.submit_report(type="CRASH", description="Accident with a bus, lanes blocked.", road=self.r_tb)
        self.assertEqual(second.possible_duplicate_of_id, first.id)
        self.assertIsNone(first.possible_duplicate_of_id)

    @override_settings(INCIDENT_REPORT_RATE="2/hour")
    def test_rate_limit(self):
        for i in range(2):
            ok = self.client.post("/api/incidents/report", self.report_payload(description=f"Crash report number {i} here"), format="json")
            self.assertEqual(ok.status_code, 201)
        blocked = self.client.post("/api/incidents/report", self.report_payload(description="Yet another crash report"), format="json")
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.json()["code"], "throttled")
        self.assertIn("wait", blocked.json()["detail"])
