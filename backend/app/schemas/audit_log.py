from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
