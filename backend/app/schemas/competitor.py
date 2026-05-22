from typing import Optional
from pydantic import BaseModel

class CompetitorBase(BaseModel):
    name: str
    website: str
    youtube_url: Optional[str] = None
    instagram_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    reddit_url: Optional[str] = None
    twitter_url: Optional[str] = None
    medium_url: Optional[str] = None
    threads_url: Optional[str] = None
    status: Optional[str] = "active"
    region: Optional[str] = "Global"

class CompetitorCreate(CompetitorBase):
    company_id: int

class CompetitorUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    youtube_url: Optional[str] = None
    instagram_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    reddit_url: Optional[str] = None
    twitter_url: Optional[str] = None
    medium_url: Optional[str] = None
    threads_url: Optional[str] = None
    status: Optional[str] = None
    region: Optional[str] = None

class CompetitorOut(CompetitorBase):
    id: int
    company_id: int

    class Config:
        from_attributes = True
