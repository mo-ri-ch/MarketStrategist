from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Insight(Base, TimestampMixin):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    competitor_id = Column(Integer, ForeignKey("competitors.id", ondelete="CASCADE"), nullable=True)
    insight_type = Column(String, index=True, nullable=False)  # social, news, market, general
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    sentiment_score = Column(Float, default=0.0, nullable=False)  # between -1.0 and 1.0
    data_points = Column(JSON, nullable=True)

    # Relationships
    company = relationship("Company")
    competitor = relationship("Competitor")
