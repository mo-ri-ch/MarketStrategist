from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class PredictionBase(BaseModel):
    competitor_id: int
    predicted_action: str
    description: str
    confidence_score: float
    trigger_events: Optional[List[Dict[str, Any]]] = None

class PredictionOut(PredictionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
