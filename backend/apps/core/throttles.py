from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle


class SettingsRateThrottle(SimpleRateThrottle):
    """Throttle by client address; the rate is read from Django settings (so tests can override it)."""

    rate_setting = ""

    def get_rate(self):
        return getattr(settings, self.rate_setting)

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class IncidentReportThrottle(SettingsRateThrottle):
    scope = "incident_report"
    rate_setting = "INCIDENT_REPORT_RATE"


class LoginThrottle(SettingsRateThrottle):
    scope = "login"
    rate_setting = "LOGIN_RATE"
