from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core.deps import get_current_user, require_admin_role
from app.db.session import get_db
from app.db.models.event import Event
from app.db.models.user import Team, User
from app.db.models.register import Registration
from app.db.models.representative import EventRepresentative
from app.schemas.event import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventStatus
)
from app.schemas.user import TeamCreate, TeamUpdate, TeamResponse, AdminRepresentativeUpdate
from app.schemas.admin import EventStatistics, UserListItem
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ConflictException
)

router = APIRouter()


@router.get("/users", response_model=List[UserListItem])
async def list_all_users(
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db),
        event_id: Optional[str] = None,
):
    """[ADMIN ONLY] Accounts with registration status for the selected Event."""
    users_query = db.query(User).order_by(User.created_at.desc())
    registrations = {}
    if event_id:
        registrations = {
            registration.user_id: registration
            for registration in db.query(Registration).filter(
                Registration.event_id == event_id,
            ).all()
        }
        users_query = users_query.join(Registration, Registration.user_id == User.id).filter(
            Registration.event_id == event_id
        )
    users = users_query.all()
    return [
        UserListItem(
            id=user.id,
            emp_code=user.emp_code,
            full_name=user.full_name,
            email=user.email,
            team_name=(registrations[user.id].team.name if registrations.get(user.id) and registrations[user.id].team else (user.team.name if user.team else None)),
            work_location=user.work_location,
            is_representative=bool(event_id and registrations.get(user.id) and db.query(EventRepresentative).filter(
                EventRepresentative.user_id == user.id,
                EventRepresentative.event_id == event_id,
                EventRepresentative.team_id == registrations[user.id].team_id,
            ).first()),
            is_registered=user.id in registrations,
            is_participating=bool(registrations.get(user.id) and registrations[user.id].is_participating),
            desired_shift=registrations.get(user.id).desired_shift if registrations.get(user.id) else None,
            has_flight=bool(registrations.get(user.id) and registrations[user.id].assigned_flight_id),
            has_vehicle=bool(registrations.get(user.id) and any([
                registrations[user.id].assigned_vehicle_1_id,
                registrations[user.id].assigned_vehicle_2_id,
                registrations[user.id].assigned_vehicle_3_id,
                registrations[user.id].assigned_vehicle_4_id,
            ])),
            has_hotel=bool(registrations.get(user.id) and registrations[user.id].assigned_hotel_room),
            completion_percentage=0,
        )
        for user in users
    ]


@router.put("/users/{user_id}/representative", response_model=UserListItem)
async def update_user_representative(
        user_id: str,
        data: AdminRepresentativeUpdate,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db),
):
    """[ADMIN ONLY] Grant or revoke Gala representative permission."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException(detail="Không tìm thấy tài khoản CBNV")

    registration = db.query(Registration).filter(
        Registration.user_id == user_id,
        Registration.event_id == data.event_id,
    ).first()
    if data.is_representative and (
        not registration
        or not registration.is_participating
        or not registration.team_id
    ):
        raise ConflictException(
            detail="Chỉ user đã đăng ký tham gia Event và đã được gán Team mới được làm đại diện Gala"
        )

    if data.is_representative:
        existing_representative = db.query(EventRepresentative).filter(
            EventRepresentative.event_id == data.event_id,
            EventRepresentative.team_id == registration.team_id,
            EventRepresentative.user_id != user_id,
        ).first()
        if existing_representative:
            raise ConflictException(
                detail=(
                    "Team này đã có đại diện Gala. "
                    "Mỗi Team trong một Event chỉ được có một đại diện."
                )
            )

    assignment = db.query(EventRepresentative).filter(
        EventRepresentative.event_id == data.event_id,
        EventRepresentative.user_id == user_id,
    ).first()
    if data.is_representative and not assignment:
        db.add(EventRepresentative(event_id=data.event_id, team_id=registration.team_id, user_id=user_id))
    elif not data.is_representative and assignment:
        db.delete(assignment)

    db.commit()
    db.refresh(user)
    return UserListItem(
        id=user.id,
        emp_code=user.emp_code,
        full_name=user.full_name,
        email=user.email,
        team_name=registration.team.name if registration and registration.team else (user.team.name if user.team else None),
        work_location=user.work_location,
        is_representative=bool(data.is_representative),
        is_registered=False,
        is_participating=False,
        desired_shift=None,
        has_flight=False,
        has_vehicle=False,
        has_hotel=False,
        completion_percentage=0,
    )


# ============================================
# EVENT MANAGEMENT (Quản lý Sự kiện)
# ============================================

@router.get("/events", response_model=List[EventResponse])
async def list_all_events(
        current_user: dict = Depends(require_admin_role),  # ✅ CHỈ ADMIN
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Lấy danh sách tất cả sự kiện Team Building.

    Phân quyền: Chỉ BTC (ADMIN role) mới được xem danh sách đầy đủ.
    """
    events = db.query(Event).order_by(Event.created_at.desc()).all()

    return [_map_event_to_response(db, event) for event in events]


@router.get("/events/active", response_model=Optional[EventResponse])
async def get_active_event(
        current_user: dict = Depends(get_current_user),  # ✅ ANY AUTHENTICATED USER
        db: Session = Depends(get_db)
):
    """
    [PUBLIC FOR AUTHENTICATED USERS] Lấy sự kiện đang hoạt động (active).

    Endpoint này được gọi bởi:
    - User: Để biết có sự kiện nào đang mở đăng ký không
    - Frontend: Để quyết định hiển thị UI nào

    Phân quyền: Bất kỳ user nào đã đăng nhập đều được xem.
    """
    active_event = db.query(Event).order_by(Event.created_at.desc()).first()

    if not active_event:
        return None

    return _map_event_to_response(db, active_event)


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event_detail(
        event_id: str,
        current_user: dict = Depends(require_admin_role),  # ✅ CHỈ ADMIN
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Lấy chi tiết một sự kiện.

    Phân quyền: Chỉ BTC (ADMIN role) mới được xem chi tiết.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    return _map_event_to_response(db, event)


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
        data: EventCreate,
        current_user: dict = Depends(require_admin_role),  # ✅ CHỈ ADMIN
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Tạo sự kiện Team Building mới.

    Phân quyền: Chỉ BTC (ADMIN role) mới được tạo event.

    Validation:
    - event_date_start < event_date_end
    - registration_deadline < event_date_start
    """
    # Log audit
    print(f"[AUDIT] Admin {current_user['emp_code']} đang tạo event mới: {data.event_name}")

    # Validate dates
    if data.event_date_start >= data.event_date_end:
        raise BadRequestException(
            detail="Ngày bắt đầu phải trước ngày kết thúc"
        )

    if data.registration_deadline >= data.event_date_start:
        raise BadRequestException(
            detail="Deadline đăng ký phải trước ngày bắt đầu sự kiện"
        )

    # Tạo event mới với status DRAFT
    new_event = Event(
        name=data.event_name,
        start_date=data.event_date_start,
        end_date=data.event_date_end,
        location=data.location,
        registration_deadline=data.registration_deadline,
        description=data.description,
        status="DRAFT"  # Mặc định là DRAFT
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    print(f"[AUDIT] Event {new_event.id} đã được tạo bởi {current_user['emp_code']}")

    return _map_event_to_response(db, new_event)


@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
        event_id: str,
        data: EventUpdate,
        current_user: dict = Depends(require_admin_role),  # ✅ CHỈ ADMIN
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Cập nhật thông tin sự kiện.

    Phân quyền: Chỉ BTC (ADMIN role) mới được update event.

    Validation:
    - Không cho phép update nếu status = ALLOCATION_COMPLETED
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    # Log audit
    print(f"[AUDIT] Admin {current_user['emp_code']} đang cập nhật event {event_id}")

    # Không cho phép update nếu đã hoàn thành phân bổ
    if event.status == "ALLOCATION_COMPLETED" and data.status != "ALLOCATION_COMPLETED":
        raise BadRequestException(
            detail="Không thể chỉnh sửa sự kiện đã hoàn thành phân bổ"
        )

    # Update các trường
    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)

    return _map_event_to_response(db, event)


@router.put("/events/{event_id}/status")
async def update_event_status(
        event_id: str,
        new_status: EventStatus,
        current_user: dict = Depends(require_admin_role),  # ✅ CHỈ ADMIN
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Cập nhật trạng thái sự kiện (State Machine).

    Phân quyền: Chỉ BTC (ADMIN role) mới được thay đổi status.

    WORKFLOW:
    1. DRAFT → REGISTRATION_OPEN (Mở đăng ký)
    2. REGISTRATION_OPEN → REGISTRATION_CLOSED (Đóng đăng ký)
    3. REGISTRATION_CLOSED → ALLOCATION_IN_PROGRESS (Đang phân bổ)
    4. ALLOCATION_IN_PROGRESS → ALLOCATION_COMPLETED (Hoàn thành phân bổ)
    5. ALLOCATION_COMPLETED → EVENT_ACTIVE (Sự kiện đang diễn ra)
    6. EVENT_ACTIVE → EVENT_COMPLETED (Sự kiện kết thúc)
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    # Log audit
    print(f"[AUDIT] Admin {current_user['emp_code']} đang chuyển status event {event_id} "
          f"từ {event.status} → {new_status}")

    # Validate state transition
    allowed_transitions = {
        "DRAFT": ["REGISTRATION_OPEN"],
        "REGISTRATION_OPEN": ["REGISTRATION_CLOSED", "DRAFT"],
        "REGISTRATION_CLOSED": ["ALLOCATION_IN_PROGRESS", "REGISTRATION_OPEN"],
        "ALLOCATION_IN_PROGRESS": ["ALLOCATION_COMPLETED", "REGISTRATION_CLOSED"],
        "ALLOCATION_COMPLETED": ["EVENT_ACTIVE"],
        "EVENT_ACTIVE": ["EVENT_COMPLETED"],
        "EVENT_COMPLETED": []
    }

    current_status = event.status

    if new_status not in allowed_transitions.get(current_status, []):
        raise BadRequestException(
            detail=f"Không thể chuyển từ '{current_status}' sang '{new_status}'. "
                   f"Trạng thái hợp lệ: {allowed_transitions.get(current_status, [])}"
        )

    # Update status
    event.status = new_status
    db.commit()
    db.refresh(event)

    return {
        "success": True,
        "event_id": event.id,
        "old_status": current_status,
        "new_status": new_status,
        "changed_by": current_user['emp_code'],
        "message": f"Đã chuyển trạng thái sự kiện từ '{current_status}' sang '{new_status}'"
    }


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
        event_id: str,
        current_user: dict = Depends(require_admin_role),  # ✅ CHỈ ADMIN
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Xóa sự kiện.

    Phân quyền: Chỉ BTC (ADMIN role) mới được xóa event.

    Validation:
    - Chỉ cho phép xóa nếu status = DRAFT (chưa có ai đăng ký)
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    # Log audit
    print(f"[AUDIT] Admin {current_user['emp_code']} đang XÓA event {event_id} ({event.name})")

    if event.status != "DRAFT":
        raise BadRequestException(
            detail="Chỉ có thể xóa sự kiện ở trạng thái DRAFT (chưa mở đăng ký)"
        )

    db.delete(event)
    db.commit()

    print(f"[AUDIT] Event {event_id} đã bị xóa bởi {current_user['emp_code']}")

    return None


def _map_event_to_response(db: Session, event: Event) -> EventResponse:
    """Helper function map Event model sang EventResponse schema"""
    from app.db.models.register import Registration

    # Đếm số người đã đăng ký
    total_participants = db.query(Registration).filter(
        Registration.event_id == event.id,
        Registration.is_participating == True
    ).count()

    return EventResponse(
        id=event.id,
        event_name=event.name,
        event_date_start=event.start_date,
        event_date_end=event.end_date,
        location=event.location or "Chưa xác định",
        registration_deadline=event.registration_deadline or event.start_date,
        description=event.description,
        status=event.status,
        total_participants=total_participants,
        created_at=event.created_at
    )


# ============================================
# TEAM MANAGEMENT (Quản lý Team/Bộ phận)
# ============================================

@router.get("/teams", response_model=List[TeamResponse])
async def list_teams(
        event_id: str = None,
        current_user: dict = Depends(require_admin_role),  # ✅ CHỈ ADMIN
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Lấy danh sách tất cả Team/Bộ phận.

    Phân quyền: Chỉ BTC (ADMIN role) mới được xem danh sách teams.
    """
    if event_id:
        teams = db.query(Team).filter(Team.event_id == event_id).all()
    else:
        teams = db.query(Team).all()

    return [_map_team_to_response(db, team) for team in teams]


@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
        data: TeamCreate,
        current_user: dict = Depends(require_admin_role),  # ✅ CHỈ ADMIN
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Tạo Team/Bộ phận mới.

    Phân quyền: Chỉ BTC (ADMIN role) mới được tạo team.
    """
    print(f"[AUDIT] Admin {current_user['emp_code']} đang tạo team: {data.team_name}")

    # Validate event tồn tại
    event = db.query(Event).filter(Event.id == data.event_id).first()
    if not event:
        raise NotFoundException(detail="Sự kiện không tồn tại")

    # Check duplicate team_name
    existing = db.query(Team).filter(
        Team.event_id == data.event_id,
        Team.name == data.team_name
    ).first()

    if existing:
        raise ConflictException(
            detail=f"Team '{data.team_name}' đã tồn tại trong sự kiện này"
        )

    # Tạo team mới
    new_team = Team(
        event_id=data.event_id,
        name=data.team_name
    )

    db.add(new_team)
    db.commit()
    db.refresh(new_team)

    return _map_team_to_response(db, new_team)


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
        team_id: str,
        current_user: dict = Depends(require_admin_role),  # ✅ CHỈ ADMIN
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Xóa Team.

    Phân quyền: Chỉ BTC (ADMIN role) mới được xóa team.

    Validation:
    - Không cho phép xóa nếu còn user thuộc team này
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise NotFoundException(detail="Không tìm thấy team")

    print(f"[AUDIT] Admin {current_user['emp_code']} đang XÓA team {team_id} ({team.name})")

    # Check xem còn user nào thuộc team không
    member_count = db.query(Registration).filter(
        Registration.team_id == team_id,
        Registration.event_id == team.event_id,
    ).count()

    if member_count > 0:
        raise BadRequestException(
            detail=f"Không thể xóa team này. Còn {member_count} thành viên. "
                   "Vui lòng chuyển họ sang team khác trước."
        )

    db.delete(team)
    db.commit()

    return None


def _map_team_to_response(db: Session, team: Team) -> TeamResponse:
    """Helper function map Team model sang TeamResponse schema"""
    member_count = db.query(Registration).filter(
        Registration.team_id == team.id,
        Registration.event_id == team.event_id,
        Registration.is_participating.is_(True),
    ).count()

    return TeamResponse(
        id=team.id,
        team_name=team.name,
        event_id=team.event_id,
        member_count=member_count,
        created_at=team.created_at
    )


# ============================================
# EVENT STATISTICS (Thống kê sự kiện)
# ============================================

@router.get("/events/{event_id}/stats", response_model=EventStatistics)
async def get_event_statistics(
        event_id: str,
        current_user: dict = Depends(require_admin_role),  # ✅ CHỈ ADMIN
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Lấy thống kê chi tiết của một sự kiện.

    Phân quyền: Chỉ BTC (ADMIN role) mới được xem statistics.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    from app.db.models.register import Registration
    from app.db.models.resource import Flight, Vehicle
    from app.db.models.gala import GalaSeat

    # Thống kê đăng ký
    total_registered = db.query(Registration).filter(
        Registration.event_id == event_id
    ).count()

    total_participating = db.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.is_participating == True
    ).count()

    # Thống kê chuyến bay
    flights = db.query(Flight).filter(Flight.event_id == event_id).all()
    total_flight_slots = sum(f.total_slots for f in flights)

    allocated_flight_slots = db.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.assigned_flight_id != None
    ).count()

    # Thống kê Gala
    gala_seats = db.query(GalaSeat).filter(GalaSeat.event_id == event_id).all()
    total_gala_seats = len(gala_seats)
    confirmed_gala_seats = len([s for s in gala_seats if s.status == "CONFIRMED"])

    # Thống kê khách sạn
    total_hotel_rooms_assigned = db.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.assigned_hotel_room != None
    ).count()

    return EventStatistics(
        event_id=event.id,
        event_name=event.name,
        status=event.status,
        total_registered=total_registered,
        total_participating=total_participating,
        total_flights=len(flights),
        total_flight_slots=total_flight_slots,
        allocated_flight_slots=allocated_flight_slots,
        available_flight_slots=total_flight_slots - allocated_flight_slots,
        vehicle_stats_route_1={},
        vehicle_stats_route_2={},
        vehicle_stats_route_3={},
        vehicle_stats_route_4={},
        total_gala_seats=total_gala_seats,
        confirmed_gala_seats=confirmed_gala_seats,
        available_gala_seats=total_gala_seats - confirmed_gala_seats,
        total_hotel_rooms_assigned=total_hotel_rooms_assigned,
        last_updated=datetime.utcnow()
    )
