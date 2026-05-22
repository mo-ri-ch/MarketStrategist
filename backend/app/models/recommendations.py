from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Recommendation(Base, TimestampMixin):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    trigger_event_id = Column(Integer, ForeignKey("competitor_events.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    strategic_action = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    priority = Column(String, default="medium", nullable=False)  # low, medium, high
    status = Column(String, default="pending", nullable=False)    # pending, implemented, dismissed

    # Relationships
    company = relationship("Company")
    trigger_event = relationship("CompetitorEvent")
