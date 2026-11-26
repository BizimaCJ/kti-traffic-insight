from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

from apps.audit.models import AuditAction, AuditLog
from tests.helpers import PASSWORD, KtiTestCase, make_admin


class AuthTests(KtiTestCase):
    def setUp(self):
        super().setUp()
        self.admin = make_admin()
        self.client = APIClient(enforce_csrf_checks=True)

    def csrf_headers(self):
        self.client.get("/api/auth/session")
        return {"HTTP_X_CSRFTOKEN": self.client.cookies["csrftoken"].value}

    def login(self, username="admin", password=PASSWORD, headers=True):
        extra = self.csrf_headers() if headers else {}
        return self.client.post("/api/auth/login", {"username": username, "password": password}, format="json", **extra)

    def test_session_endpoint_reports_anonymous_and_sets_csrf_cookie(self):
        body = self.client.get("/api/auth/session").json()
        self.assertFalse(body["authenticated"])
        self.assertEqual(body["session_timeout_minutes"], 15)
        self.assertIn("csrftoken", self.client.cookies)

    def test_login_needs_csrf_token(self):
        self.assertEqual(self.login(headers=False).status_code, 403)

    def test_login_success_is_audited_and_session_is_reported(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["full_name"], "Admin One")
        self.assertEqual(AuditLog.objects.get().action, AuditAction.LOGIN)
        self.assertTrue(self.client.get("/api/auth/session").json()["authenticated"])
        self.assertEqual(self.client.get("/api/admin/incidents").status_code, 200)

    def test_wrong_password_and_unknown_user_look_the_same(self):
        for username, password in [("admin", "wrong-password-1"), ("nobody", PASSWORD)]:
            with self.subTest(username=username):
                response = self.login(username, password)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["detail"], "Incorrect username or password.")
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_non_staff_account_cannot_log_in_to_admin(self):
        make_admin("visitor", staff=False)
        self.assertEqual(self.login("visitor").status_code, 400)

    def test_inactive_account_cannot_log_in(self):
        get_user_model().objects.filter(username="admin").update(is_active=False)
        self.assertEqual(self.login().status_code, 400)

    def test_logout_ends_session_and_is_audited(self):
        self.login()
        headers = {"HTTP_X_CSRFTOKEN": self.client.cookies["csrftoken"].value}
        self.assertEqual(self.client.post("/api/auth/logout", **headers).status_code, 200)
        self.assertEqual(self.client.get("/api/admin/incidents").status_code, 401)
        self.assertEqual(list(AuditLog.objects.order_by("id").values_list("action", flat=True)),
                         [AuditAction.LOGIN, AuditAction.LOGOUT])

    def test_admin_actions_need_csrf_token_once_logged_in(self):
        self.login()
        response = self.client.post("/api/admin/alerts", {"message": "Alert without token"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_session_expires_after_15_minutes_of_inactivity(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 15 * 60)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)  # activity extends the session

    @override_settings(LOGIN_RATE="3/min")
    def test_login_attempts_are_rate_limited(self):
        codes = [self.login(password="wrong-password-1").status_code for _ in range(4)]
        self.assertEqual(codes, [400, 400, 400, 429])
