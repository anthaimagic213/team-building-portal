from datetime import datetime
from typing import List, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.db.models.event import Event
from app.db.models.gala import GalaSeat
from app.db.models.hotel import Hotel, HotelRoom
from app.db.models.register import Registration
from app.db.models.resource import Flight, Vehicle
from app.db.models.user import User, Team
from app.schemas.admin import (
    EventStatistics,
    FlightStatistics,
    TeamStatistics,
    UserListItem,
    VehicleStatistics,
)



def get_event_statistics(
        db: Session,
        event_id: str,
) -> EventStatistics:
    """
    Lấy thống kê tổng quan của Event.
    """

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundException(detail="Không tìm thấy Event")

    # 1. Tổng số CBNV
    total_employees = db.query(User).count()

    # 2. Số đã đăng ký
    total_registered = (
        db.query(Registration)
        .filter(Registration.event_id == event_id)
        .count()
    )

    # 3. Số tham gia
    total_participating = (
        db.query(Registration)
        .filter(
            Registration.event_id == event_id,
            Registration.is_participating.is_(True),
        )
        .count()
    )

    registration_rate = (
        (total_registered / total_employees * 100)
        if total_employees > 0
        else 0
    )

    # 4. Đăng ký theo Ca
    shift_1_count = (
        db.query(Registration)
        .filter(
            Registration.event_id == event_id,
            Registration.is_participating.is_(True),
            Registration.desired_shift == "SHIFT_1",
        )
        .count()
    )

    shift_2_count = (
        db.query(Registration)
        .filter(
            Registration.event_id == event_id,
            Registration.is_participating.is_(True),
            Registration.desired_shift == "SHIFT_2",
        )
        .count()
    )

    no_shift = (
        db.query(Registration)
        .filter(
            Registration.event_id == event_id,
            Registration.is_participating.is_(True),
            Registration.desired_shift.is_(None),
        )
        .count()
    )

    # 5. Thống kê chuyến bay
    flights = (
        db.query(Flight)
        .filter(Flight.event_id == event_id)
        .all()
    )

    total_flights = len(flights)
    total_flight_slots = sum(f.total_slots for f in flights)

    allocated_flight_slots = (
        db.query(Registration)
        .filter(
            Registration.event_id == event_id,
            Registration.is_participating.is_(True),
            (Registration.assigned_outbound_flight_id.isnot(None) | Registration.assigned_flight_id.isnot(None)),
        )
        .count()
    )
    unallocated_flight_users = total_participating - allocated_flight_slots
    unallocated_flight_user_ids = [r.user_id for r in db.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.is_participating.is_(True),
        Registration.assigned_outbound_flight_id.is_(None),
    ).all()]

    available_flight_slots = total_flight_slots - allocated_flight_slots

    flight_utilization = (
        (allocated_flight_slots / total_flight_slots * 100)
        if total_flight_slots > 0
        else 0
    )

    # 6. Thống kê xe theo chặng
    vehicle_stats = {}

    for route in ["ROUTE_1", "ROUTE_2", "ROUTE_3", "ROUTE_4"]:
        route_field_map = {
            "ROUTE_1": ("need_vehicle_route_1", "assigned_vehicle_1_id"),
            "ROUTE_2": ("need_vehicle_route_2", "assigned_vehicle_2_id"),
            "ROUTE_3": ("need_vehicle_route_3", "assigned_vehicle_3_id"),
            "ROUTE_4": ("need_vehicle_route_4", "assigned_vehicle_4_id"),
        }

        need_col, assign_col = route_field_map[route]

        need_count = (
            db.query(Registration)
            .filter(
                Registration.event_id == event_id,
                Registration.is_participating.is_(True),
                getattr(Registration, need_col).is_(True),
            )
            .count()
        )

        allocated_count = (
            db.query(Registration)
            .filter(
                Registration.event_id == event_id,
                Registration.is_participating.is_(True),
                getattr(Registration, assign_col).isnot(None),
            )
            .count()
        )

        vehicle_stats[f"vehicle_stats_{route.lower()}"] = {
            "need": need_count,
            "allocated": allocated_count,
            "unallocated": need_count - allocated_count,
        }

    # 7. Thống kê Gala
    gala_seats = (
        db.query(GalaSeat)
        .filter(GalaSeat.event_id == event_id)
        .all()
    )

    total_gala_seats = len(gala_seats)
    confirmed_gala = sum(
        1 for s in gala_seats
        if s.status == "CONFIRMED"
    )
    available_gala = total_gala_seats - confirmed_gala

    # 8. Thống kê khách sạn
    total_hotel_rooms = (
        db.query(HotelRoom)
        .join(Hotel)
        .filter(Hotel.event_id == event_id)
        .count()
    )

    hotel_rooms_assigned = (
        db.query(Registration)
        .filter(
            Registration.event_id == event_id,
            Registration.is_participating.is_(True),
            Registration.assigned_hotel_room.isnot(None),
        )
        .count()
    )

    return EventStatistics(
        event_id=event.id,
        event_name=event.name,
        event_status=event.status,
        total_employees=total_employees,
        total_registered=total_registered,
        total_participating=total_participating,
        registration_rate=round(registration_rate, 2),
        shift_1_count=shift_1_count,
        shift_2_count=shift_2_count,
        no_shift_preference=no_shift,
        total_flights=total_flights,
        total_flight_slots=total_flight_slots,
        allocated_flight_slots=allocated_flight_slots,
        available_flight_slots=available_flight_slots,
        flight_utilization_rate=round(flight_utilization, 2),
        unallocated_flight_users=max(0, unallocated_flight_users),
        unallocated_flight_user_ids=unallocated_flight_user_ids,
        allocation_warnings=([f"Có {unallocated_flight_users} người chưa được phân bổ chuyến bay đi"] if unallocated_flight_users > 0 else []),
        vehicle_stats_route_1=vehicle_stats["vehicle_stats_route_1"],
        vehicle_stats_route_2=vehicle_stats["vehicle_stats_route_2"],
        vehicle_stats_route_3=vehicle_stats["vehicle_stats_route_3"],
        vehicle_stats_route_4=vehicle_stats["vehicle_stats_route_4"],
        total_gala_seats=total_gala_seats,
        confirmed_gala_seats=confirmed_gala,
        available_gala_seats=available_gala,
        total_hotel_rooms=total_hotel_rooms,
        total_hotel_rooms_assigned=hotel_rooms_assigned,
        last_updated=datetime.utcnow(),
    )


def get_team_statistics(
        db: Session,
        event_id: str,
) -> List[TeamStatistics]:
    """
    Thống kê theo Team.
    """

    teams = (
        db.query(Team)
        .filter(Team.event_id == event_id)
        .all()
    )

    result = []

    for team in teams:
        team_registrations = db.query(Registration).filter(
            Registration.event_id == event_id,
            Registration.team_id == team.id,
        ).all()
        member_ids = [registration.user_id for registration in team_registrations]
        total_members = len(team_registrations)

        registered = (
            db.query(Registration)
            .filter(
                Registration.event_id == event_id,
                Registration.user_id.in_(member_ids),
            )
            .count()
        )

        participating = (
            db.query(Registration)
            .filter(
                Registration.event_id == event_id,
                Registration.user_id.in_(member_ids),
                Registration.is_participating.is_(True),
            )
            .count()
        )

        allocated_flight = (
            db.query(Registration)
            .filter(
                Registration.event_id == event_id,
                Registration.user_id.in_(member_ids),
                Registration.is_participating.is_(True),
                Registration.assigned_flight_id.isnot(None),
            )
            .count()
        )

        allocated_vehicle = (
            db.query(Registration)
            .filter(
                Registration.event_id == event_id,
                Registration.user_id.in_(member_ids),
                Registration.is_participating.is_(True),
                Registration.assigned_vehicle_1_id.isnot(None),
            )
            .count()
        )

        allocated_hotel = (
            db.query(Registration)
            .filter(
                Registration.event_id == event_id,
                Registration.user_id.in_(member_ids),
                Registration.is_participating.is_(True),
                Registration.assigned_hotel_room.isnot(None),
            )
            .count()
        )

        has_gala = (
                       db.query(GalaSeat)
                       .filter(
                           GalaSeat.event_id == event_id,
                           GalaSeat.locked_by_team_id == team.id,
                           GalaSeat.status == "CONFIRMED",
                       )
                       .first()
                   ) is not None

        completion = 0
        if participating > 0:
            checklist = [
                allocated_flight,
                allocated_vehicle,
                allocated_hotel,
            ]
            completion = sum(checklist) / len(checklist) / participating * 100

        result.append(
            TeamStatistics(
                team_id=team.id,
                team_name=team.name,
                total_members=total_members,
                registered_members=registered,
                participating_members=participating,
                allocated_flight=allocated_flight,
                allocated_vehicle=allocated_vehicle,
                allocated_hotel=allocated_hotel,
                has_gala_seat=has_gala,
                completion_rate=round(completion, 2),
            )
        )

    return result


def get_user_list(
        db: Session,
        event_id: str,
        team_id: Optional[str] = None,
        work_location: Optional[str] = None,
        has_registered: Optional[bool] = None,
) -> List[UserListItem]:
    """
    Lấy danh sách CBNV với filter.
    """

    query = db.query(User)

    if team_id:
        query = query.filter(User.team_id == team_id)

    if work_location:
        query = query.filter(User.work_location == work_location)

    users = query.all()

    result = []

    for user in users:
        registration = (
            db.query(Registration)
            .filter(
                Registration.user_id == user.id,
                Registration.event_id == event_id,
            )
            .first()
        )

        is_registered = registration is not None

        if has_registered is not None and is_registered != has_registered:
            continue

        is_participating = registration.is_participating if registration else False
        desired_shift = registration.desired_shift if registration else None

        has_flight = (
            registration.assigned_flight_id is not None
            if registration
            else False
        )

        has_vehicle = any([
            registration.assigned_vehicle_1_id if registration else None,
            registration.assigned_vehicle_2_id if registration else None,
        ])

        has_hotel = (
            registration.assigned_hotel_room is not None
            if registration
            else False
        )

        checklist = [has_flight, has_vehicle, has_hotel]
        completion = int(sum(checklist) / len(checklist) * 100)

        team_name = user.team.name if user.team else None

        result.append(
            UserListItem(
                id=user.id,
                emp_code=user.emp_code,
                full_name=user.full_name,
                email=user.email,
                phone=user.phone,
                team_name=team_name,
                work_location=user.work_location,
                is_registered=is_registered,
                is_participating=is_participating,
                desired_shift=desired_shift,
                has_flight=has_flight,
                has_vehicle=has_vehicle,
                has_hotel=has_hotel,
                completion_percentage=completion,
            )
        )

    return result
