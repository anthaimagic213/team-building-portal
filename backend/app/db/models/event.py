from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base, generate_uuid


class Event(Base):
    __tablename__ = "events"

    id = Column(
        String,
        primary_key=True,
        default=generate_uuid,
        index=True,
    )

    name = Column(
        String,
        nullable=False,
    )

    status = Column(
        String,
        nullable=False,
        default="DRAFT",
        index=True,
    )

    start_date = Column(
        DateTime,
        nullable=True,
    )

    end_date = Column(
        DateTime,
        nullable=True,
    )

    location = Column(
        String,
        nullable=True,
    )

    registration_deadline = Column(
        DateTime,
        nullable=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    # Event -> Teams
    teams = relationship(
        "Team",
        back_populates="event",
        cascade="all, delete-orphan",
    )

    # Event -> Flights
    flights = relationship(
        "Flight",
        back_populates="event",
        cascade="all, delete-orphan",
    )

    # Event -> Vehicles
    vehicles = relationship(
        "Vehicle",
        back_populates="event",
        cascade="all, delete-orphan",
    )

    # Event -> Hotels
    hotels = relationship(
        "Hotel",
        back_populates="event",
        cascade="all, delete-orphan",
    )
