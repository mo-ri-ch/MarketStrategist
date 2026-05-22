from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class AlertBase(BaseModel):
    competitor_id: int
    event_id: int
    is_read: bool = False

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    is_read: Optional[bool] = None

class EventAlertInfo(BaseModel):
    id: int
    event_type: str
    title: str
    description: str
    severity: str
    confidence_score: float
    created_at: datetime

    class Config:
        from_attributes = True

class CompetitorAlertInfo(BaseModel):
    id: int
    name: str
    website: str

    class Config:
        from_attributes = True

class AlertOut(AlertBase):
    id: int
    created_at: datetime
    competitor: CompetitorAlertInfo
    event: EventAlertInfo

    class Config:
        from_attributes = True
