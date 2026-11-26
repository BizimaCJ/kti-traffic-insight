"""Alert rules (SRS section 4.3.3).

1. An alert is created when an incident is verified.
2. An alert is created when the delay on a road reaches the threshold (once per rise: if an
   administrator withdraws it, it does not come back until the delay has dropped and risen again).
3. Administrators can publish and withdraw alerts by hand.
Automatic alerts are withdrawn by the system when their cause is gone (delay back under the
threshold, or incident resolved).
"""
from typing import Dict, Iterable

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.alerts.models import Alert, AlertStatus, AlertTrigger
from apps.audit import services as audit
from apps.audit.models import AuditAction
from apps.core.exceptions import Conflict, DomainError


def list_active():
    return Alert.objects.filter(status=AlertStatus.ACTIVE).select_related("road", "incident")


# ---------------------------------------------------------------- administrator actions
@transaction.atomic
def publish_manual(admin, message: str, road=None) -> Alert:
    message = " ".join((message or "").split())
    if len(message) < 5:
        raise DomainError("Please write an alert message (at least 5 characters).", code="message_required")
    alert = Alert.objects.create(
        message=message[:300], trigger_type=AlertTrigger.MANUAL, road=road, published_by=admin,
    )
    audit.record(admin, AuditAction.PUBLISH_ALERT, "Alert", alert.pk, alert.message)
    return alert


@transaction.atomic
def withdraw(alert: Alert, admin) -> Alert:
    alert = Alert.objects.select_for_update().get(pk=alert.pk)
    if alert.status != AlertStatus.ACTIVE:
        raise Conflict("This alert has already been withdrawn.", code="already_withdrawn")
    alert.status = AlertStatus.WITHDRAWN
    alert.withdrawn_at = timezone.now()
    alert.withdrawn_by = admin
    alert.save(update_fields=["status", "withdrawn_at", "withdrawn_by"])
    audit.record(admin, AuditAction.WITHDRAW_ALERT, "Alert", alert.pk, alert.message)
    return alert


# ---------------------------------------------------------------- automatic rules
def on_incident_verified(incident) -> Alert:
    """Rule 1: a verified incident creates an Active alert."""
    label = incident.get_type_display()
    return Alert.objects.create(
        message=f"{label} on {incident.road.name}. Expect delays.",
        trigger_type=AlertTrigger.INCIDENT_VERIFIED, incident=incident, road=incident.road,
    )


def withdraw_for_incident(incident) -> int:
    """When an incident is resolved its alert is no longer needed."""
    return Alert.objects.filter(incident=incident, status=AlertStatus.ACTIVE).update(
        status=AlertStatus.WITHDRAWN, withdrawn_at=timezone.now()
    )


def evaluate_delay_rules(new_conditions: Iterable, previous_by_road: Dict[int, object]) -> dict:
    """Rule 2: compare each new reading with the previous one for the same road."""
    threshold = settings.ALERT_DELAY_THRESHOLD
    created = cleared = 0
    for condition in new_conditions:
        active = Alert.objects.filter(
            road_id=condition.road_id, trigger_type=AlertTrigger.DELAY_THRESHOLD, status=AlertStatus.ACTIVE
        )
        if condition.delay_minutes >= threshold:
            previous = previous_by_road.get(condition.road_id)
            rising = previous is None or previous.delay_minutes < threshold
            if rising and not active.exists():
                Alert.objects.create(
                    message=f"Heavy delays on {condition.road.name}: about {condition.delay_minutes} minutes extra.",
                    trigger_type=AlertTrigger.DELAY_THRESHOLD, road=condition.road, traffic_condition=condition,
                )
                created += 1
        else:
            cleared += active.update(status=AlertStatus.WITHDRAWN, withdrawn_at=timezone.now())
    return {"created": created, "cleared": cleared}
