from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Competitor(Base, TimestampMixin):
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False, index=True)
    website = Column(String, nullable=False)
    
    # Social channels URLs
    youtube_url = Column(String, nullable=True)
    instagram_url = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    facebook_url = Column(String, nullable=True)
    reddit_url = Column(String, nullable=True)
    twitter_url = Column(String, nullable=True)
    medium_url = Column(String, nullable=True)
    threads_url = Column(String, nullable=True)
    
    status = Column(String, default="active", nullable=False)  # active, archived
    region = Column(String, default="Global", nullable=False)

    # Relationships
    company = relationship("Company", back_populates="competitors")
    events = relationship("CompetitorEvent", back_populates="competitor", cascade="all, delete-orphan")
