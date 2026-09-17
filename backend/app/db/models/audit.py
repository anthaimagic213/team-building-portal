"""
Audit Log Model
"""

from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.db.base import Base, generate_uuid


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)

    user_id = Column(String, nullable=False, index=True)
    emp_code = Column(String, nullable=False)

    action = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=True, index=True)

    old_data = Column(JSON, nullable=True)
    new_data = Column(JSON, nullable=True)

    reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
