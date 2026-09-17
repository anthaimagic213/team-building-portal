"""Seed chuyến bay và xe mẫu cho các event development.

Chạy từ thư mục ``backend`` sau khi đã seed event/team/user:

    python seed_resources.py

Script idempotent, có thể chạy nhiều lần mà không tạo bản ghi trùng.
"""

from datetime import datetime, timedelta

from app.db.models.event import Event
from app.db.models.resource import Flight, Vehicle
from app.db.session import SessionLocal


EVENT_NAMES = [
    "Team Building Da Nang 2026",
    "Company Trip Nha Trang 2026",
    "Annual Retreat Phu Quoc 2026",
    "Team Building Ha Long 2027",
]

DESTINATIONS = {
    "Da Nang": ("HAN", "DAD", "Sân bay Đà Nẵng", "Khách sạn Đà Nẵng"),
    "Nha Trang": ("HAN", "CXR", "Sân bay Cam Ranh", "Khách sạn Nha Trang"),
    "Phu Quoc": ("SGN", "PQC", "Sân bay Phú Quốc", "Khách sạn Phú Quốc"),
    "Ha Long": ("HAN", "VDO", "Sân bay Vân Đồn", "Khách sạn Hạ Long"),
}

ROUTES = {
    "ROUTE_1": ("Văn phòng công ty", "Sân bay khởi hành", 45),
    "ROUTE_2": ("Sân bay đến", "Khách sạn", 45),
    "ROUTE_3": ("Khách sạn", "Sân bay đến", 45),
    "ROUTE_4": ("Sân bay khởi hành", "Văn phòng công ty", 45),
}


def seed_resources() -> tuple[int, int]:
    db = SessionLocal()
    created_flights = created_vehicles = 0
    try:
        events = db.query(Event).filter(Event.name.in_(EVENT_NAMES)).all()
        if not events:
            raise RuntimeError("Chưa có event mẫu. Hãy chạy `python seed_dev.py --full` trước.")

        for event_index, event in enumerate(sorted(events, key=lambda item: item.name), start=1):
            origin, destination, airport_name, hotel_name = DESTINATIONS.get(
                event.location, ("HAN", "DAD", "Sân bay đến", "Khách sạn")
            )
            base_time = event.start_date or datetime.now() + timedelta(days=30)

            flights = [
                (f"TB{event_index:02d}01", "OUTBOUND", origin, destination, 9, 11),
                (f"TB{event_index:02d}02", "OUTBOUND", origin, destination, 14, 16),
                (f"TB{event_index:02d}03", "RETURN", destination, origin, 15, 17),
                (f"TB{event_index:02d}04", "RETURN", destination, origin, 19, 21),
            ]
            for code, direction, flight_origin, flight_destination, departure_hour, arrival_hour in flights:
                if db.query(Flight).filter(Flight.event_id == event.id, Flight.flight_code == code).first():
                    continue
                departure = base_time.replace(hour=departure_hour, minute=0, second=0, microsecond=0)
                arrival = base_time.replace(hour=arrival_hour, minute=0, second=0, microsecond=0)
                if arrival <= departure:
                    arrival += timedelta(days=1)
                db.add(Flight(
                    event_id=event.id,
                    flight_code=code,
                    direction=direction,
                    departure_time=departure,
                    arrival_time=arrival,
                    origin=flight_origin,
                    destination=flight_destination,
                    total_slots=90,
                ))
                created_flights += 1

            for route_index, (route_type, (pickup, dropoff, capacity)) in enumerate(ROUTES.items(), start=1):
                for vehicle_index in range(1, 3):
                    vehicle_name = f"E{event_index:02d} {route_type} - Bus {vehicle_index:02d}"
                    exists = db.query(Vehicle).filter(
                        Vehicle.event_id == event.id,
                        Vehicle.vehicle_name == vehicle_name,
                        Vehicle.route_type == route_type,
                    ).first()
                    if exists:
                        continue
                    departure = base_time.replace(
                        hour={"ROUTE_1": 6, "ROUTE_2": 11, "ROUTE_3": 14, "ROUTE_4": 20}[route_type],
                        minute=30 if vehicle_index == 2 else 0,
                        second=0,
                        microsecond=0,
                    )
                    db.add(Vehicle(
                        event_id=event.id,
                        vehicle_name=vehicle_name,
                        route_type=route_type,
                        departure_time=departure,
                        pickup_location=pickup.replace("Sân bay khởi hành", origin).replace("Sân bay đến", airport_name),
                        dropoff_location=dropoff.replace("Sân bay khởi hành", origin).replace("Sân bay đến", airport_name).replace("Khách sạn", hotel_name),
                        capacity=capacity,
                        notes="Xe mẫu phục vụ kiểm thử phân bổ tự động.",
                    ))
                    created_vehicles += 1

        db.commit()
        return created_flights, created_vehicles
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    flights, vehicles = seed_resources()
    print(f"✅ Đã tạo mới: {flights} chuyến bay, {vehicles} xe")
    print("✅ Seed resources hoàn tất!")