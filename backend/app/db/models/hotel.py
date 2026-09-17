from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, generate_uuid


class Hotel(Base):
    __tablename__ = "hotels"

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

    hotel_name = Column(
        String,
        nullable=False,
    )

    address = Column(
        String,
        nullable=True,
    )

    phone = Column(
        String,
        nullable=True,
    )

    total_rooms = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # Khớp với Event.hotels
    event = relationship(
        "Event",
        back_populates="hotels",
    )

    # Hotel -> HotelRoom
    rooms = relationship(
        "HotelRoom",
        back_populates="hotel",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "hotel_name",
            name="uq_hotel_event_name",
        ),
    )


class HotelRoom(Base):
    __tablename__ = "hotel_rooms"

    id = Column(
        String,
        primary_key=True,
        default=generate_uuid,
        index=True,
    )

    hotel_id = Column(
        String,
        ForeignKey("hotels.id"),
        nullable=False,
        index=True,
    )

    room_code = Column(
        String,
        nullable=False,
    )

    room_type = Column(
        String,
        nullable=True,
    )

    capacity = Column(
        Integer,
        nullable=False,
        default=2,
    )

    # Danh sách user ID, hiện đang lưu dạng chuỗi phân cách bằng dấu phẩy
    assigned_user_ids = Column(
        Text,
        nullable=True,
    )

    # Khớp với Hotel.rooms
    hotel = relationship(
        "Hotel",
        back_populates="rooms",
    )

    __table_args__ = (
        UniqueConstraint(
            "hotel_id",
            "room_code",
            name="uq_hotel_room_code",
        ),
    )
