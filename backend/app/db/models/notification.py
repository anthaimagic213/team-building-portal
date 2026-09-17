from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base, generate_uuid


class Notification(Base):
    """
    Thông báo từ BTC đến CBNV.

    Loại thông báo:
    - INFO: Thông báo thông thường
    - WARNING: Cảnh báo
    - URGENT: Khẩn cấp
    """
    __tablename__ = "notifications"

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

    # Nếu target_user_id = None thì gửi cho toàn bộ CBNV
    target_user_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # Nếu target_team_id có giá trị thì gửi cho toàn bộ Team
    target_team_id = Column(
        String,
        ForeignKey("teams.id"),
        nullable=True,
        index=True,
    )

    title = Column(
        String,
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    notification_type = Column(
        String,
        nullable=False,
        default="INFO",
        index=True,
    )

    created_by = Column(
        String,
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    event = relationship("Event")
    target_user = relationship("User", foreign_keys=[target_user_id])
    target_team = relationship("Team", foreign_keys=[target_team_id])
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index(
            "ix_notifications_event_created",
            "event_id",
            "created_at",
        ),
    )


class UserNotificationRead(Base):
    """
    Tracking xem user đã đọc notification nào chưa.
    """
    __tablename__ = "user_notification_reads"

    id = Column(
        String,
        primary_key=True,
        default=generate_uuid,
        index=True,
    )

    user_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    notification_id = Column(
        String,
        ForeignKey("notifications.id"),
        nullable=False,
        index=True,
    )

    read_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user = relationship("User")
    notification = relationship("Notification")

    __table_args__ = (
        Index(
            "ix_user_notification_unique",
            "user_id",
            "notification_id",
            unique=True,
        ),
    )
