"""Incident business rules: anonymous reporting (FR 3) and the administrator workflow
(FR 7, 8, 14, 15). Every administrator action writes an audit entry (FR 18) in the same transaction."""
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.alerts import services as alert_services
from apps.audit import services as audit
from apps.audit.models import AuditAction
from apps.core.exceptions import Conflict, DomainError
from apps.incidents.models import Incident, IncidentStatus, IncidentType
from apps.incidents.status import can_transition

ACTIVE_STATUSES = (IncidentStatus.SUBMITTED, IncidentStatus.UNDER_REVIEW, IncidentStatus.VERIFIED)


class DuplicateReport(Conflict):
    code = "duplicate"


class InvalidTransition(Conflict):
    code = "invalid_transition"


def list_public():
    """Business rule: road users only see Verified incidents (Resolved ones disappear)."""
    return Incident.objects.filter(status=IncidentStatus.VERIFIED).select_related("road", "intersection")


# ---------------------------------------------------------------- anonymous reporting
def submit_report(*, type: str, description: str, road, intersection=None,
                  reporter_name: str = "", reporter_contact: str = "", now=None) -> Incident:
    """Save an anonymous report with status Submitted.

    - The same report sent twice within a few minutes is refused (double-click or resend).
    - A similar active report on the same road and type is accepted but flagged for the administrator.
    """
    now = now or timezone.now()
    description = " ".join(description.split())
    window_start = now - timedelta(minutes=settings.DUPLICATE_WINDOW_MINUTES)
    if Incident.objects.filter(
        road=road, type=type, description__iexact=description, reported_at__gte=window_start, is_simulated=False
    ).exists():
        raise DuplicateReport("You already sent this report a moment ago. Thank you, we have it.")
    similar = (
        Incident.objects.filter(road=road, type=type, status__in=ACTIVE_STATUSES, is_simulated=False)
        .order_by("-reported_at").first()
    )
    return Incident.objects.create(
        type=type, description=description, road=road, intersection=intersection,
        reporter_name=reporter_name.strip(), reporter_contact=reporter_contact.strip(),
        reported_at=now, status=IncidentStatus.SUBMITTED, possible_duplicate_of=similar,
    )


# ---------------------------------------------------------------- administrator workflow
def _locked(incident: Incident) -> Incident:
    return Incident.objects.select_for_update(of=("self",)).select_related("road", "intersection").get(pk=incident.pk)


def _move(incident: Incident, new_status: str) -> None:
    if not can_transition(incident.status, new_status):
        label = IncidentStatus(new_status).label.lower()
        raise InvalidTransition(f"This incident is {IncidentStatus(incident.status).label.lower()}, so it cannot be moved to {label}.")
    incident.status = new_status


@transaction.atomic
def start_review(incident: Incident, admin) -> Incident:
    incident = _locked(incident)
    _move(incident, IncidentStatus.UNDER_REVIEW)
    incident.reviewed_by = admin
    incident.save(update_fields=["status", "reviewed_by"])
    audit.record(admin, AuditAction.REVIEW_INCIDENT, "Incident", incident.pk, "Submitted -> Under review")
    return incident


@transaction.atomic
def verify(incident: Incident, admin) -> Incident:
    incident = _locked(incident)
    _move(incident, IncidentStatus.VERIFIED)
    incident.reviewed_by = admin
    incident.verified_at = timezone.now()
    incident.save(update_fields=["status", "reviewed_by", "verified_at"])
    audit.record(admin, AuditAction.VERIFY_INCIDENT, "Incident", incident.pk, "Under review -> Verified")
    alert_services.on_incident_verified(incident)
    return incident


@transaction.atomic
def reject(incident: Incident, admin, reason: str) -> Incident:
    reason = (reason or "").strip()
    if not reason:
        raise DomainError("A rejection reason is required.", code="reason_required")
    incident = _locked(incident)
    previous = IncidentStatus(incident.status).label
    _move(incident, IncidentStatus.REJECTED)
    incident.reviewed_by = admin
    incident.rejection_reason = reason
    incident.save(update_fields=["status", "reviewed_by", "rejection_reason"])
    audit.record(admin, AuditAction.REJECT_INCIDENT, "Incident", incident.pk, f"{previous} -> Rejected: {reason}")
    return incident


@transaction.atomic
def resolve(incident: Incident, admin) -> Incident:
    incident = _locked(incident)
    _move(incident, IncidentStatus.RESOLVED)
    incident.save(update_fields=["status"])
    audit.record(admin, AuditAction.UPDATE_INCIDENT_STATUS, "Incident", incident.pk, "Verified -> Resolved")
    alert_services.withdraw_for_incident(incident)
    return incident


ACTIONS = {"review": start_review, "verify": verify, "resolve": resolve}
