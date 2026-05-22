"""
Audit Log Model — stores immutable logs of system interactions and configurations.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from app.models.base import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(String, nullable=False, index=True)
    details = Column(JSON, nullable=True)  # Detailed payload or query details
    ip_address = Column(String, nullable=True)
