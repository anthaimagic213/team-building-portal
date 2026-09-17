from sqlalchemy import Column, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base, generate_uuid


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)

    is_participating = Column(Boolean, default=True)
    desired_shift = Column(String, nullable=True)

    need_vehicle_route_1 = Column(Boolean, default=False)
    need_vehicle_route_2 = Column(Boolean, default=False)
    need_vehicle_route_3 = Column(Boolean, default=False)
    need_vehicle_route_4 = Column(Boolean, default=False)

    # ✅ THÊM 2 CỘT NÀY để lưu địa điểm đón khách hàng mong muốn
    pickup_location_route_1 = Column(String, nullable=True)
    pickup_location_route_4 = Column(String, nullable=True)

    wishes = Column(Text, nullable=True)

    assigned_flight_id = Column(String, ForeignKey("flights.id"), nullable=True)
    assigned_outbound_flight_id = Column(String, ForeignKey("flights.id"), nullable=True)
    assigned_return_flight_id = Column(String, ForeignKey("flights.id"), nullable=True)
    assigned_vehicle_1_id = Column(String, ForeignKey("vehicles.id"), nullable=True)
    assigned_vehicle_2_id = Column(String, ForeignKey("vehicles.id"), nullable=True)
    assigned_vehicle_3_id = Column(String, ForeignKey("vehicles.id"), nullable=True)
    assigned_vehicle_4_id = Column(String, ForeignKey("vehicles.id"), nullable=True)

    assigned_hotel_room = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="registrations")
    team = relationship("Team")
    flight = relationship("Flight", foreign_keys=[assigned_flight_id])
    outbound_flight = relationship("Flight", foreign_keys=[assigned_outbound_flight_id])
    return_flight = relationship("Flight", foreign_keys=[assigned_return_flight_id])
    vehicle_1 = relationship("Vehicle", foreign_keys=[assigned_vehicle_1_id])
    vehicle_2 = relationship("Vehicle", foreign_keys=[assigned_vehicle_2_id])
    vehicle_3 = relationship("Vehicle", foreign_keys=[assigned_vehicle_3_id])
    vehicle_4 = relationship("Vehicle", foreign_keys=[assigned_vehicle_4_id])
