"""
Memory Model — stores persistent user/company context for the CEO Assistant.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class Memory(Base, TimestampMixin):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # e.g. "user_preferences", "company_goals", "conversation_context"
    key = Column(String, nullable=False, index=True)
    # Flexible JSON blob for structured data
    value = Column(JSON, nullable=True)

    # Relationships
    company = relationship("Company")
