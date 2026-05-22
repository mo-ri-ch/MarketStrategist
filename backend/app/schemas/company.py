from typing import Optional
from pydantic import BaseModel

class CompanyBase(BaseModel):
    name: str
    website: str
    industry: Optional[str] = None
    services: Optional[str] = None
    region: Optional[str] = None
    goals: Optional[str] = None
    webhook_url: Optional[str] = None
    notification_email: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    services: Optional[str] = None
    region: Optional[str] = None
    goals: Optional[str] = None
    webhook_url: Optional[str] = None
    notification_email: Optional[str] = None

class CompanyOut(CompanyBase):
    id: int
    user_id: int
    ai_summary: Optional[str] = None

    class Config:
        from_attributes = True
