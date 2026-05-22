"""
Competitor Prediction Model — stores forecast next actions for competitors.
"""

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class CompetitorPrediction(Base, TimestampMixin):
    __tablename__ = "competitor_predictions"

    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(
        Integer,
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    predicted_action = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False, default=0.5)
    trigger_events = Column(JSON, nullable=True)  # List/dict of events that triggered this prediction

    # Relationships
    competitor = relationship("Competitor")
