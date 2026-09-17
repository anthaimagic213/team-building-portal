from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.schemas.journey import MyJourneyResponse, JourneySummary, JourneyEventItem
from app.db.models import Event, Team, Registration, User
from app.db.models.representative import EventRepresentative
from app.db.models.gala import GalaConfig, GalaTeamTurn
from app.db.models.resource import Flight, Vehicle
from app.services import journey_svc

router = APIRouter()


@router.get("/events", response_model=list[JourneyEventItem])
def list_user_events(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    """List every event and the authenticated user's registration state."""
    user_id = current_user["sub"]
    events = db.query(Event).order_by(Event.start_date.desc()).all()
    result = []
    for event in events:
        registration = db.query(Registration).filter(
            Registration.user_id == user_id,
            Registration.event_id == event.id,
        ).first()
        participant_count = db.query(Registration).filter(
            Registration.event_id == event.id,
            Registration.is_participating.is_(True),
        ).count()
        outbound = db.query(Flight).filter(Flight.id == registration.assigned_outbound_flight_id, Flight.event_id == event.id).first() if registration and registration.assigned_outbound_flight_id else None
        returning = db.query(Flight).filter(Flight.id == registration.assigned_return_flight_id, Flight.event_id == event.id).first() if registration and registration.assigned_return_flight_id else None
        vehicle_ids = [registration.assigned_vehicle_1_id, registration.assigned_vehicle_2_id, registration.assigned_vehicle_3_id, registration.assigned_vehicle_4_id] if registration else []
        vehicles = db.query(Vehicle).filter(Vehicle.id.in_([value for value in vehicle_ids if value]), Vehicle.event_id == event.id).all() if any(vehicle_ids) else []
        vehicle_by_id = {vehicle.id: vehicle for vehicle in vehicles}
        hotel_room = None
        if registration and registration.assigned_hotel_room:
            from app.db.models.hotel import HotelRoom, Hotel
            hotel_room = db.query(HotelRoom).join(Hotel).filter(Hotel.event_id == event.id, HotelRoom.room_code == registration.assigned_hotel_room).first()
        gala_seat = db.query(__import__('app.db.models.gala', fromlist=['GalaSeat']).GalaSeat).filter(
            __import__('app.db.models.gala', fromlist=['GalaSeat']).GalaSeat.event_id == event.id,
            __import__('app.db.models.gala', fromlist=['GalaSeat']).GalaSeat.locked_by_user_id == user_id,
            __import__('app.db.models.gala', fromlist=['GalaSeat']).GalaSeat.status.in_(['LOCKING', 'CONFIRMED']),
        ).first()
        can_manage_gala = bool(
            registration
            and registration.is_participating
            and registration.team_id
            and event.status not in ("DRAFT", "REGISTRATION_OPEN")
            and db.query(GalaConfig).filter(
                GalaConfig.event_id == event.id,
                GalaConfig.is_enabled.is_(True),
                GalaConfig.turn_status == "ACTIVE",
            ).first()
            and db.query(GalaTeamTurn).filter(
                GalaTeamTurn.event_id == event.id,
                GalaTeamTurn.team_id == registration.team_id,
                GalaTeamTurn.status == "ACTIVE",
                GalaTeamTurn.turn_number == db.query(GalaConfig.current_turn_number).filter(
                    GalaConfig.event_id == event.id,
                ).scalar_subquery(),
            ).first()
        )
        result.append(JourneyEventItem(
            id=event.id,
            event_name=event.name,
            event_date_start=event.start_date,
            event_date_end=event.end_date,
            location=event.location,
            registration_deadline=event.registration_deadline,
            status=event.status,
            teams=[{"id": team.id, "team_name": team.name} for team in event.teams],
            participant_count=participant_count,
            can_manage_gala=can_manage_gala,
            registration={
                "id": registration.id,
                "team_id": registration.team_id,
                "is_participating": registration.is_participating,
                "assigned_flight_id": registration.assigned_flight_id,
                "assigned_outbound_flight_id": registration.assigned_outbound_flight_id,
                "assigned_return_flight_id": registration.assigned_return_flight_id,
                "assigned_vehicle_1_id": registration.assigned_vehicle_1_id,
                "assigned_vehicle_2_id": registration.assigned_vehicle_2_id,
                "assigned_vehicle_3_id": registration.assigned_vehicle_3_id,
                "assigned_vehicle_4_id": registration.assigned_vehicle_4_id,
                "hotel_room_code": registration.assigned_hotel_room,
                "outbound_flight": {"flight_code": outbound.flight_code, "departure_time": outbound.departure_time, "arrival_time": outbound.arrival_time, "origin": outbound.origin, "destination": outbound.destination} if outbound else None,
                "return_flight": {"flight_code": returning.flight_code, "departure_time": returning.departure_time, "arrival_time": returning.arrival_time, "origin": returning.origin, "destination": returning.destination} if returning else None,
                "vehicles": [{"route_type": route, "vehicle_name": vehicle_by_id[value].vehicle_name, "departure_time": vehicle_by_id[value].departure_time, "pickup_location": vehicle_by_id[value].pickup_location, "dropoff_location": vehicle_by_id[value].dropoff_location} for route, value in zip(("ROUTE_1", "ROUTE_2", "ROUTE_3", "ROUTE_4"), vehicle_ids) if value in vehicle_by_id],
                "hotel": {"hotel_name": hotel_room.hotel.hotel_name, "room_code": hotel_room.room_code, "room_type": hotel_room.room_type} if hotel_room else None,
                "gala_seat": {"seat_code": gala_seat.seat_code, "table_code": gala_seat.table_code, "seat_position": gala_seat.seat_position, "status": gala_seat.status} if gala_seat else None,
            } if registration else None,
        ))
    return result


@router.get(
    "/me",
    response_model=MyJourneyResponse,
)
def get_my_journey(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
        event_id: str | None = None,
):
    """
    [USER] Lấy toàn bộ thông tin hành trình cá nhân.

    Endpoint này tổng hợp:
    - Thông tin cá nhân và Team
    - Chuyến bay đi/về
    - Xe 4 chặng
    - Khách sạn & phòng
    - Gala Dinner
    - Lịch trình tổng thể
    - Thông báo mới nhất
    """

    user_id = current_user.get("sub")
    event_id = event_id or current_user.get("active_event_id")

    if not user_id:
        raise NotFoundException(detail="Token không chứa user_id")

    if not event_id:
        raise NotFoundException(detail="Token không chứa active_event_id")

    return journey_svc.get_my_journey(
        db=db,
        user_id=user_id,
        event_id=event_id,
    )


@router.get(
    "/summary",
    response_model=JourneySummary,
)
def get_journey_summary(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
        event_id: str | None = None,
):
    """
    [USER] Lấy tóm tắt hành trình.

    Dùng cho widget/dashboard nhỏ.
    """

    user_id = current_user.get("sub")
    event_id = event_id or current_user.get("active_event_id")

    if not user_id:
        raise NotFoundException(detail="Token không chứa user_id")

    if not event_id:
        raise NotFoundException(detail="Token không chứa active_event_id")

    return journey_svc.get_journey_summary(
        db=db,
        user_id=user_id,
        event_id=event_id,
    )


@router.post(
    "/notifications/{notification_id}/read",
)
def mark_notification_read(
        notification_id: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    """
    [USER] Đánh dấu thông báo đã đọc.
    """

    user_id = current_user.get("sub")

    if not user_id:
        raise NotFoundException(detail="Token không chứa user_id")

    journey_svc.mark_notification_as_read(
        db=db,
        user_id=user_id,
        notification_id=notification_id,
    )

    return {
        "success": True,
        "message": "Đã đánh dấu thông báo đã đọc",
    }
