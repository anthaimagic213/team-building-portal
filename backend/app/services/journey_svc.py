from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.db.models.event import Event
from app.db.models.gala import GalaSeat
from app.db.models.representative import EventRepresentative
from app.db.models.hotel import Hotel, HotelRoom
from app.db.models.notification import Notification, UserNotificationRead
from app.db.models.register import Registration
from app.db.models.resource import Flight, Vehicle
from app.db.models.schedule import EventSchedule
from app.db.models.user import User, Team
from app.schemas.journey import (
    EventScheduleItem,
    JourneyFlightInfo,
    JourneyGalaInfo,
    JourneyHotelInfo,
    JourneySummary,
    JourneyVehicleInfo,
    MyJourneyResponse,
    NotificationItem,
)


def get_my_journey(
        db: Session,
        user_id: str,
        event_id: str,
) -> MyJourneyResponse:
    """
    Lấy toàn bộ thông tin hành trình của CBNV.

    Args:
        db: Database session
        user_id: UUID của user
        event_id: UUID của event

    Returns:
        MyJourneyResponse với đầy đủ thông tin
    """

    # 1. Lấy thông tin User
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise NotFoundException(detail="Không tìm thấy user")

    # 2. Lấy thông tin Event
    event = (
        db.query(Event)
        .filter(Event.id == event_id)
        .first()
    )

    if not event:
        raise NotFoundException(detail="Không tìm thấy event")

    # 3. Lấy thông tin Registration
    registration = (
        db.query(Registration)
        .filter(
            Registration.user_id == user_id,
            Registration.event_id == event_id,
        )
        .first()
    )

    if not registration:
        raise NotFoundException(
            detail="User chưa có đăng ký cho event này"
        )

    # 4. Lấy thông tin Team
    team_name = None
    team_leader = None

    registration_team_id = registration.team_id or user.team_id
    if registration_team_id:
        team = (
            db.query(Team)
            .filter(Team.id == registration_team_id)
            .first()
        )

        if team:
            team_name = team.name

            # Tìm team leader (user có is_representative = True)
            leader = db.query(User).join(EventRepresentative, EventRepresentative.user_id == User.id).filter(
                EventRepresentative.team_id == team.id,
                EventRepresentative.event_id == registration.event_id,
            ).first()
            if leader:
                team_leader = leader.full_name

    # 5. Lấy thông tin chuyến bay
    outbound_flight = None
    return_flight = None

    flight_ids = [registration.assigned_outbound_flight_id, registration.assigned_return_flight_id]
    if registration.assigned_flight_id:
        flight_ids.append(registration.assigned_flight_id)
    for flight_id in dict.fromkeys(filter(None, flight_ids)):
        flight = (
            db.query(Flight)
            .filter(Flight.id == flight_id, Flight.event_id == event_id)
            .first()
        )

        if flight:
            flight_info = JourneyFlightInfo(
                flight_code=flight.flight_code,
                direction=flight.direction,
                departure_time=flight.departure_time,
                arrival_time=flight.arrival_time,
                origin=flight.origin,
                destination=flight.destination,
            )

            if flight.direction == "OUTBOUND" and outbound_flight is None:
                outbound_flight = flight_info
            elif flight.direction == "RETURN" and return_flight is None:
                return_flight = flight_info

    # 6. Lấy thông tin xe 4 chặng
    vehicles_info = []

    vehicle_map = {
        "ROUTE_1": registration.assigned_vehicle_1_id,
        "ROUTE_2": registration.assigned_vehicle_2_id,
        "ROUTE_3": registration.assigned_vehicle_3_id,
        "ROUTE_4": registration.assigned_vehicle_4_id,
    }

    for route_type, vehicle_id in vehicle_map.items():
        if vehicle_id:
            vehicle = (
                db.query(Vehicle)
                .filter(Vehicle.id == vehicle_id)
                .first()
            )

            if vehicle:
                captain_name = None
                captain_phone = None

                if vehicle.captain_id:
                    captain = (
                        db.query(User)
                        .filter(User.id == vehicle.captain_id)
                        .first()
                    )

                    if captain:
                        captain_name = captain.full_name
                        captain_phone = captain.phone

                vehicles_info.append(
                    JourneyVehicleInfo(
                        vehicle_name=vehicle.vehicle_name,
                        route_type=route_type,
                        departure_time=vehicle.departure_time,
                        pickup_location=vehicle.pickup_location,
                        dropoff_location=vehicle.dropoff_location,
                        captain_name=captain_name,
                        captain_phone=captain_phone,
                        notes=vehicle.notes,
                    )
                )

    # Sắp xếp xe theo chặng
    vehicles_info.sort(key=lambda v: v.route_type)

    # 7. Lấy thông tin khách sạn
    hotel_info = None

    if registration.assigned_hotel_room:
        # assigned_hotel_room lưu room_code
        room = (
            db.query(HotelRoom)
            .join(Hotel)
            .filter(
                Hotel.event_id == event_id,
                HotelRoom.room_code == registration.assigned_hotel_room,
            )
            .first()
        )

        if room and room.hotel:
            # Lấy danh sách người ở cùng phòng
            roommates = []

            if room.assigned_user_ids:
                user_ids = [
                    uid.strip()
                    for uid in room.assigned_user_ids.split(",")
                    if uid.strip()
                ]

                roommate_users = (
                    db.query(User)
                    .filter(User.id.in_(user_ids))
                    .all()
                )

                roommates = [
                    u.full_name
                    for u in roommate_users
                    if u.id != user_id
                ]

            hotel_info = JourneyHotelInfo(
                hotel_name=room.hotel.hotel_name,
                address=room.hotel.address,
                phone=room.hotel.phone,
                room_code=room.room_code,
                room_type=room.room_type,
                roommates=roommates,
            )

    # 8. Lấy thông tin Gala Dinner
    gala_info = None

    if registration_team_id:
        gala_seat = (
            db.query(GalaSeat)
            .filter(
                GalaSeat.event_id == event_id,
                GalaSeat.locked_by_user_id == user_id,
                GalaSeat.status.in_(["CONFIRMED", "LOCKING"]),
            )
            .first()
        )

        if gala_seat:
            gala_info = JourneyGalaInfo(
                seat_code=gala_seat.seat_code,
                table_code=gala_seat.table_code,
                seat_position=gala_seat.seat_position,
                status=gala_seat.status,
            )

    # 9. Lấy lịch trình sự kiện
    schedule_items = (
        db.query(EventSchedule)
        .filter(EventSchedule.event_id == event_id)
        .order_by(EventSchedule.schedule_time.asc())
        .all()
    )

    schedule = [
        EventScheduleItem(
            time=item.schedule_time,
            title=item.title,
            description=item.description,
            location=item.location,
        )
        for item in schedule_items
    ]

    # 10. Lấy thông báo
    notifications_data = _get_user_notifications(
        db=db,
        user_id=user_id,
        event_id=event_id,
    )

    # 11. Xác định registration status
    registration_status = "CONFIRMED" if registration.is_participating else "CANCELLED"

    return MyJourneyResponse(
        user_name=user.full_name,
        emp_code=user.emp_code,
        email=user.email,
        phone=user.phone,
        team_name=team_name,
        team_leader=team_leader,
        event_name=event.name,
        event_date_start=event.start_date,
        event_date_end=event.end_date,
        event_location=event.location or "Chưa cập nhật",
        event_status=event.status,
        is_participating=registration.is_participating,
        registration_status=registration_status,
        outbound_flight=outbound_flight,
        return_flight=return_flight,
        vehicles=vehicles_info,
        hotel=hotel_info,
        gala_seat=gala_info,
        schedule=schedule,
        notifications=notifications_data,
        last_updated=datetime.utcnow(),
    )


def get_journey_summary(
        db: Session,
        user_id: str,
        event_id: str,
) -> JourneySummary:
    """
    Lấy tóm tắt hành trình (dùng cho widget/dashboard).
    """

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise NotFoundException(detail="Không tìm thấy user")

    registration = (
        db.query(Registration)
        .filter(
            Registration.user_id == user_id,
            Registration.event_id == event_id,
        )
        .first()
    )

    if not registration:
        raise NotFoundException(detail="Chưa có đăng ký")

    registration_team_id = registration.team_id or user.team_id
    team_name = None

    if registration_team_id:
        team = (
            db.query(Team)
            .filter(Team.id == registration_team_id)
            .first()
        )

        if team:
            team_name = team.name

    has_flight = bool(registration.assigned_outbound_flight_id or registration.assigned_return_flight_id or registration.assigned_flight_id)
    has_vehicle = any([
        registration.assigned_vehicle_1_id,
        registration.assigned_vehicle_2_id,
        registration.assigned_vehicle_3_id,
        registration.assigned_vehicle_4_id,
    ])
    has_hotel = registration.assigned_hotel_room is not None

    has_gala_seat = False
    if registration_team_id:
        gala_seat = (
            db.query(GalaSeat)
            .filter(
                GalaSeat.event_id == event_id,
                GalaSeat.locked_by_team_id == registration_team_id,
                GalaSeat.status == "CONFIRMED",
            )
            .first()
        )
        has_gala_seat = gala_seat is not None

    # Tính completion percentage
    checklist = [has_flight, has_vehicle, has_hotel, has_gala_seat]
    completion = int((sum(checklist) / len(checklist)) * 100)

    return JourneySummary(
        user_name=user.full_name,
        emp_code=user.emp_code,
        team_name=team_name,
        has_flight=has_flight,
        has_vehicle=has_vehicle,
        has_hotel=has_hotel,
        has_gala_seat=has_gala_seat,
        completion_percentage=completion,
    )


def _get_user_notifications(
        db: Session,
        user_id: str,
        event_id: str,
        limit: int = 10,
) -> List[NotificationItem]:
    """
    Lấy danh sách thông báo cho user.

    Bao gồm:
    - Thông báo gửi cho toàn bộ CBNV (target_user_id = None)
    - Thông báo gửi cho Team của user
    - Thông báo gửi riêng cho user
    """

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        return []

    # Lấy notifications
    from sqlalchemy import or_

    query = db.query(Notification).filter(
        Notification.event_id == event_id,
        or_(
            Notification.target_user_id.is_(None),  # Gửi cho toàn bộ
            Notification.target_user_id == user_id,  # Gửi riêng
            Notification.target_team_id == registration_team_id,  # Gửi cho Team theo Event
        ),
    )

    notifications = (
        query
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []

    for notif in notifications:
        # Kiểm tra user đã đọc chưa
        read_record = (
            db.query(UserNotificationRead)
            .filter(
                UserNotificationRead.user_id == user_id,
                UserNotificationRead.notification_id == notif.id,
            )
            .first()
        )

        result.append(
            NotificationItem(
                id=notif.id,
                title=notif.title,
                content=notif.content,
                notification_type=notif.notification_type,
                created_at=notif.created_at,
                is_read=read_record is not None,
            )
        )

    return result


def mark_notification_as_read(
        db: Session,
        user_id: str,
        notification_id: str,
) -> None:
    """
    Đánh dấu notification đã đọc.
    """

    existing = (
        db.query(UserNotificationRead)
        .filter(
            UserNotificationRead.user_id == user_id,
            UserNotificationRead.notification_id == notification_id,
        )
        .first()
    )

    if not existing:
        read_record = UserNotificationRead(
            user_id=user_id,
            notification_id=notification_id,
        )
        db.add(read_record)
        db.commit()
