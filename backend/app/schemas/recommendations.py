from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class RecommendationBase(BaseModel):
    title: str
    strategic_action: str
    rationale: str
    priority: str = "medium"
    status: str = "pending"

class RecommendationCreate(RecommendationBase):
    company_id: int
    trigger_event_id: Optional[int] = None

class RecommendationUpdate(BaseModel):
    status: Optional[str] = None  # pending, implemented, dismissed

class RecommendationOut(RecommendationBase):
    id: int
    company_id: int
    trigger_event_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
