"""
Audit Log Helper — functions to record system interactions and configurations.
"""

import logging
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

logger = logging.getLogger("market-strategist-audit")

def log_action(
    db: Session,
    user_id: Optional[int],
    action: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """
    Inserts and commits an audit log entry safely.
    """
    try:
        db_log = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to write audit log action='{action}' for user_id={user_id}: {e}")
        raise e
