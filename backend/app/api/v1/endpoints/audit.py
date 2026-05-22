from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogOut
from app.api.deps import check_role
from app.core.rate_limiter import RateLimiter

router = APIRouter()

@router.get("/", response_model=List[AuditLogOut], dependencies=[Depends(RateLimiter(limit=100, window=60, limit_by_ip=True))])
def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter logs by user ID"),
    action: Optional[str] = Query(None, description="Filter logs by action name"),
    limit: int = Query(50, ge=1, le=100, description="Limit result count"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_role(["admin"]))
):
    """
    Retrieve chronological system audit logs. Restricted to admins.
    """
    query = db.query(AuditLog)
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if action is not None:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    
    return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
