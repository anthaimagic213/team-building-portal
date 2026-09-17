from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Text,
    Integer,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base, generate_uuid


class EventSchedule(Base):
    """
    Lịch trình chương trình Team Building.

    Ví dụ:
    - 08:00 - Tập trung tại văn phòng
    - 10:30 - Bay đến Đà Nẵng
    - 14:00 - Check-in khách sạn
    - 19:00 - Gala Dinner
    """
    __tablename__ = "event_schedules"

    id = Column(
        String,
        primary_key=True,
        default=generate_uuid,
        index=True,
    )

    event_id = Column(
        String,
        ForeignKey("events.id"),
        nullable=False,
        index=True,
    )

    schedule_time = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    title = Column(
        String,
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    location = Column(
        String,
        nullable=True,
    )

    # Thứ tự hiển thị
    display_order = Column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    event = relationship("Event")
