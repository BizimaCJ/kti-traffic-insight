from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.incidents.models import Incident
from apps.network.models import Road
from apps.traffic.models import TrafficCondition


class AlertTrigger(models.TextChoices):
    INCIDENT_VERIFIED = "INCIDENT_VERIFIED", "Incident verified"
    DELAY_THRESHOLD = "DELAY_THRESHOLD", "Delay threshold reached"
    MANUAL = "MANUAL", "Published by administrator"


class AlertStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    WITHDRAWN = "WITHDRAWN", "Withdrawn"


class Alert(models.Model):
    message = models.CharField(max_length=300)
    trigger_type = models.CharField(max_length=30, choices=AlertTrigger.choices)
    status = models.CharField(max_length=20, choices=AlertStatus.choices, default=AlertStatus.ACTIVE, db_index=True)
    published_at = models.DateTimeField(default=timezone.now)
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    road = models.ForeignKey(Road, on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts")
    incident = models.ForeignKey(Incident, on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts")
    traffic_condition = models.ForeignKey(TrafficCondition, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    # null = created or withdrawn by the system itself
    published_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    withdrawn_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    class Meta:
        ordering = ["-published_at", "-id"]

    def __str__(self):
        return f"{self.trigger_type} {self.status}: {self.message[:40]}"
