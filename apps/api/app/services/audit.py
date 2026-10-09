from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def record_audit(
    db: Session,
    organization_id: str,
    actor_user_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None,
    details: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
        )
    )
