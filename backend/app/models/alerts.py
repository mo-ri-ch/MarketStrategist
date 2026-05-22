from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(Integer, ForeignKey("competitor_events.id", ondelete="CASCADE"), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)

    # Relationships
    competitor = relationship("Competitor")
    event = relationship("CompetitorEvent")
