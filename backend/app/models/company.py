from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    website = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    services = Column(Text, nullable=True)  # Services description
    region = Column(String, nullable=True)    # Operating region
    goals = Column(Text, nullable=True)       # Strategic goals
    ai_summary = Column(Text, nullable=True)  # AI-generated company overview

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="companies")
    competitors = relationship("Competitor", back_populates="company", cascade="all, delete-orphan")
