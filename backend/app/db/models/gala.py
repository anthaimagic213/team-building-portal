from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base, generate_uuid


class GalaSeat(Base):
    """
    Ghế/bàn trong khu vực Gala Dinner.

    Trạng thái:
    - AVAILABLE: Ghế đang trống
    - LOCKING: Ghế đang được một Team giữ tạm thời
    - CONFIRMED: Ghế đã được xác nhận chính thức
    - UNAVAILABLE: Ghế không sử dụng
    """

    __tablename__ = "gala_seats"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)

    event_id = Column(
        String,
        ForeignKey("events.id"),
        nullable=False,
        index=True,
    )

    seat_code = Column(String, nullable=False)

    # Mã bàn, ví dụ: T01, T02
    table_code = Column(String, nullable=True, index=True)

    # Vị trí ghế trong bàn, ví dụ: 1, 2, 3...
    seat_position = Column(Integer, nullable=True)

    status = Column(String, nullable=False, default="AVAILABLE", index=True)

    locked_by_team_id = Column(
        String,
        ForeignKey("teams.id"),
        nullable=True,
        index=True,
    )

    locked_by_user_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    locked_at = Column(DateTime, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    event = relationship("Event")
    team = relationship("Team")

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "seat_code",
            name="uq_gala_seat_event_seat_code",
        ),
    )


class GalaConfig(Base):
    """
    Cấu hình Gala Dinner cho từng Event.
    """

    __tablename__ = "gala_configs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)

    event_id = Column(
        String,
        ForeignKey("events.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # BTC bật/tắt chức năng chọn ghế
    is_enabled = Column(Boolean, nullable=False, default=False)

    # Số giây Team được giữ ghế trước khi hết hạn
    lock_duration_seconds = Column(
        Integer,
        nullable=False,
        default=300,
    )

    # Số giây dành cho mỗi lượt Team
    turn_duration_seconds = Column(
        Integer,
        nullable=False,
        default=300,
    )

    # WAITING, ACTIVE, COMPLETED
    turn_status = Column(
        String,
        nullable=False,
        default="WAITING",
    )

    current_turn_number = Column(Integer, nullable=True)

    turn_started_at = Column(DateTime, nullable=True)

    rows = Column(Integer, nullable=False, default=0)
    columns = Column(Integer, nullable=False, default=0)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    event = relationship("Event")


class GalaTeamTurn(Base):
    """
    Thứ tự bốc thăm/chọn ghế của các Team.
    """

    __tablename__ = "gala_team_turns"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)

    event_id = Column(
        String,
        ForeignKey("events.id"),
        nullable=False,
        index=True,
    )

    team_id = Column(
        String,
        ForeignKey("teams.id"),
        nullable=False,
        index=True,
    )

    turn_number = Column(Integer, nullable=False)

    # WAITING, ACTIVE, COMPLETED, SKIPPED
    status = Column(
        String,
        nullable=False,
        default="WAITING",
    )

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    event = relationship("Event")
    team = relationship("Team")

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "team_id",
            name="uq_gala_team_turn_event_team",
        ),
        UniqueConstraint(
            "event_id",
            "turn_number",
            name="uq_gala_team_turn_event_number",
        ),
    )
