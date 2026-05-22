from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class CompetitorEvent(Base, TimestampMixin):
    __tablename__ = "competitor_events"

    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String, index=True, nullable=False)  # pricing, product, hiring, news, social, general
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    original_text_diff = Column(Text, nullable=True)
    confidence_score = Column(Float, default=1.0, nullable=False)
    severity = Column(String, default="low", nullable=False)  # low, medium, high
    region = Column(String, default="Global", nullable=False)

    # Relationships
    competitor = relationship("Competitor", back_populates="events")
