from sqlalchemy import Column, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.db.base import Base, generate_uuid


class EventRepresentative(Base):
    """The user authorised to represent one team in one event."""
    __tablename__ = "event_representatives"
    __table_args__ = (
        UniqueConstraint("event_id", "team_id", name="uq_event_representative_team"),
        UniqueConstraint("event_id", "user_id", name="uq_event_representative_user"),
    )

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False, index=True)
    team_id = Column(String, ForeignKey("teams.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())