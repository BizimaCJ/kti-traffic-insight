from django.conf import settings
from django.db import models


class AuditAction(models.TextChoices):
    LOGIN = "LOGIN", "Login"
    LOGOUT = "LOGOUT", "Logout"
    REVIEW_INCIDENT = "REVIEW_INCIDENT", "Started review"
    VERIFY_INCIDENT = "VERIFY_INCIDENT", "Verified incident"
    REJECT_INCIDENT = "REJECT_INCIDENT", "Rejected incident"
    UPDATE_INCIDENT_STATUS = "UPDATE_INCIDENT_STATUS", "Updated incident status"
    PUBLISH_ALERT = "PUBLISH_ALERT", "Published alert"
    WITHDRAW_ALERT = "WITHDRAW_ALERT", "Withdrew alert"


class AuditLog(models.Model):
    """Who did what, to what, and when (FR 18). Entries are never edited or deleted by the app."""

    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="audit_entries")
    action = models.CharField(max_length=40, choices=AuditAction.choices)
    target_type = models.CharField(max_length=40, blank=True)
    target_id = models.PositiveIntegerField(null=True, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp", "-id"]

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} {self.admin} {self.action}"
