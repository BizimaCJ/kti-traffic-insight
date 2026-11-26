from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.network.models import Intersection, Road


class IncidentType(models.TextChoices):
    CRASH = "CRASH", "Crash"
    FLOODING = "FLOODING", "Flooding"
    ROADWORKS = "ROADWORKS", "Roadworks"
    BLOCKAGE = "BLOCKAGE", "Blockage"
    OTHER = "OTHER", "Other"


class IncidentStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", "Submitted"
    UNDER_REVIEW = "UNDER_REVIEW", "Under review"
    VERIFIED = "VERIFIED", "Verified"
    RESOLVED = "RESOLVED", "Resolved"
    REJECTED = "REJECTED", "Rejected"


class Incident(models.Model):
    type = models.CharField(max_length=20, choices=IncidentType.choices)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=IncidentStatus.choices, default=IncidentStatus.SUBMITTED, db_index=True)
    reported_at = models.DateTimeField(default=timezone.now)
    # Anonymous reporting: both optional (NFR 7)
    reporter_name = models.CharField(max_length=120, blank=True)
    reporter_contact = models.CharField(max_length=160, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    is_simulated = models.BooleanField(default=False)

    road = models.ForeignKey(Road, on_delete=models.PROTECT, related_name="incidents")
    intersection = models.ForeignKey(Intersection, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidents")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    possible_duplicate_of = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="possible_duplicates")

    class Meta:
        ordering = ["-reported_at", "-id"]

    @property
    def reference(self) -> str:
        return f"KTI-{self.pk:06d}"

    def __str__(self):
        return f"{self.reference} {self.type} {self.status}"
