from apps.audit.models import AuditLog


def record(admin, action: str, target_type: str = "", target_id=None, details: str = "") -> AuditLog:
    """Write one audit entry. Call this inside the same transaction as the action it describes."""
    return AuditLog.objects.create(
        admin=admin, action=action, target_type=target_type, target_id=target_id, details=details[:500]
    )
