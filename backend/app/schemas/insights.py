from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class InsightBase(BaseModel):
    insight_type: str
    title: str
    description: str
    sentiment_score: float = 0.0
    data_points: Optional[Dict[str, Any]] = None

class InsightCreate(InsightBase):
    company_id: int
    competitor_id: Optional[int] = None

class InsightOut(InsightBase):
    id: int
    company_id: int
    competitor_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
