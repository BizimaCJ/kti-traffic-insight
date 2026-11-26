from django.db import models

from apps.network.models import Road


class TrafficLevel(models.TextChoices):
    FREE_FLOW = "FREE_FLOW", "Free flow"
    MODERATE = "MODERATE", "Moderate"
    HEAVY = "HEAVY", "Heavy"
    BLOCKED = "BLOCKED", "Blocked"


class TrafficCondition(models.Model):
    """One reading of the traffic on one road. Old rows stay as history (FR 10, NFR 11)."""

    road = models.ForeignKey(Road, on_delete=models.CASCADE, related_name="conditions")
    level = models.CharField(max_length=20, choices=TrafficLevel.choices)
    average_speed_kmh = models.FloatField()
    delay_minutes = models.PositiveIntegerField()
    recorded_at = models.DateTimeField()
    is_simulated = models.BooleanField(default=True)

    class Meta:
        ordering = ["-recorded_at", "-id"]
        indexes = [models.Index(fields=["road", "recorded_at"], name="ix_traffic_road_time")]

    def __str__(self):
        return f"{self.road} {self.level} ({self.delay_minutes} min)"
