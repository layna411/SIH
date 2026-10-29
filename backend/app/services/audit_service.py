import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

logger = logging.getLogger("eduresolve.audit")

def log_audit(
    db: Session,
    action: str,
    entity_type: str,
    user_id: Optional[int] = None,
    entity_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[str] = None
) -> AuditLog:
    """Record an audit trail event."""
    if details is not None and not isinstance(details, str):
        import json
        try:
            details = json.dumps(details)
        except Exception:
            details = str(details)

    log_entry = AuditLog(
        action=action,
        entity_type=entity_type,
        user_id=user_id,
        entity_id=str(entity_id) if entity_id else None,
        ip_address=ip_address,
        details=details
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    logger.info(f"AUDIT: [{action}] {entity_type} ID={entity_id} by User={user_id}")
    return log_entry
