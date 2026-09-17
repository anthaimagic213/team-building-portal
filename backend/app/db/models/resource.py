from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base, generate_uuid


class Flight(Base):
    __tablename__ = "flights"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)

    flight_code = Column(String, nullable=False)
    direction = Column(String, nullable=False, default="OUTBOUND")  # OUTBOUND, RETURN

    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    total_slots = Column(Integer, default=0)

    event = relationship("Event", back_populates="flights")


class Vehicle(Base):
    """
    Vehicle Model - Quản lý xe đưa đón

    Hỗ trợ 4 chặng:
    - ROUTE_1: Văn phòng HN/HCM → Sân bay
    - ROUTE_2: Sân bay → Khách sạn
    - ROUTE_3: Khách sạn → Sân bay
    - ROUTE_4: Sân bay → Văn phòng HN/HCM
    """
    __tablename__ = "vehicles"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)

    vehicle_name = Column(String, nullable=False)
    route_type = Column(String, nullable=False)  # ROUTE_1, ROUTE_2, ROUTE_3, ROUTE_4

    departure_time = Column(DateTime, nullable=False)
    pickup_location = Column(String, nullable=False)
    dropoff_location = Column(String, nullable=True)

    capacity = Column(Integer, default=0)

    # Trưởng xe
    captain_id = Column(String, ForeignKey("users.id"), nullable=True)
    captain = relationship("User", foreign_keys=[captain_id])

    # Ghi chú
    notes = Column(Text, nullable=True)

    event = relationship("Event", back_populates="vehicles")
