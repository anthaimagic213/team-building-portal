from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from app.core.deps import get_current_user
from app.db.session import get_db
from app.db.models import Registration, Event, User, Team
from app.schemas.register import (
    RegistrationCreate,
    RegistrationUpdate,
    RegistrationResponse,
    CancelVehicleRequest
)
from app.core.exceptions import (
    RegistrationClosedException,
    ConflictException,
    NotFoundException,
    BadRequestException
)
from app.services import registration_svc

router = APIRouter()


@router.get("/me", response_model=Optional[RegistrationResponse])
async def get_my_registration(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
        event_id: Optional[str] = None,
):
    """
    Lấy thông tin đăng ký hiện tại của user.
    Trả về null nếu chưa đăng ký.
    """
    event_id = event_id or current_user.get("active_event_id")
    if not event_id:
        return None

    registration = db.query(Registration).filter(
        Registration.user_id == current_user["sub"],
        Registration.event_id == event_id
    ).first()

    if not registration:
        return None

    # Map sang response schema với thông tin đầy đủ
    return _map_registration_to_response(db, registration)


@router.post("/submit", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def submit_registration(
        data: RegistrationCreate,
        background_tasks: BackgroundTasks,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Nộp form đăng ký lần đầu.

    Yêu cầu:
    - User chưa đăng ký trước đó
    - Sự kiện đang ở trạng thái REGISTRATION_OPEN
    - Phải đồng ý điều khoản (agreed_to_terms = True)

    Sau khi submit thành công, hệ thống gửi email xác nhận qua BackgroundTasks.
    """
    # Validate điều khoản
    if not data.agreed_to_terms:
        raise BadRequestException(
            detail="Bạn phải đồng ý với điều khoản và quy định để tiếp tục đăng ký"
        )

    # Kiểm tra trạng thái sự kiện
    event_id = data.event_id or current_user.get("active_event_id")
    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện đang hoạt động")

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundException(detail="Sự kiện không tồn tại")

    if event.status != "REGISTRATION_OPEN":
        raise RegistrationClosedException()

    if data.is_participating and not data.team_id:
        raise BadRequestException(detail="Vui lòng chọn Team cho Event này")

    if data.team_id:
        team = db.query(Team).filter(Team.id == data.team_id, Team.event_id == event_id).first()
        if not team:
            raise BadRequestException(detail="Team không thuộc Event này")

    # Kiểm tra duplicate
    existing = db.query(Registration).filter(
        Registration.user_id == current_user["sub"],
        Registration.event_id == event_id
    ).first()

    if existing:
        raise ConflictException(
            detail="Bạn đã đăng ký rồi. Vui lòng sử dụng chức năng cập nhật thay vì đăng ký lại."
        )

    # Tạo registration mới
    new_registration = Registration(
        user_id=current_user["sub"],
        event_id=event_id,
        team_id=data.team_id,
        is_participating=data.is_participating,
        desired_shift=data.desired_shift,
        need_vehicle_route_1=data.needs_vehicle_route_1,
        need_vehicle_route_2=data.needs_vehicle_route_2,
        need_vehicle_route_3=data.needs_vehicle_route_3,
        need_vehicle_route_4=data.needs_vehicle_route_4,
        pickup_location_route_1=data.pickup_location_route_1,
        pickup_location_route_4=data.pickup_location_route_4,
        wishes=data.comments
    )

    db.add(new_registration)
    db.commit()
    db.refresh(new_registration)

    # Gửi email xác nhận (background task)
    background_tasks.add_task(
        registration_svc.send_registration_confirmation_email,
        db,
        new_registration.id
    )

    return _map_registration_to_response(db, new_registration)


@router.put("/update", response_model=RegistrationResponse)
async def update_registration(
        data: RegistrationUpdate,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Cập nhật thông tin đăng ký.

    Chỉ cho phép khi:
    - Sự kiện đang ở trạng thái REGISTRATION_OPEN
    - User đã có registration trước đó

    Không cho phép update khi status != REGISTRATION_OPEN.
    """
    event_id = data.event_id or current_user.get("active_event_id")
    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện đang hoạt động")

    # Kiểm tra trạng thái event
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event or event.status != "REGISTRATION_OPEN":
        raise RegistrationClosedException()

    # Lấy registration hiện tại
    registration = db.query(Registration).filter(
        Registration.user_id == current_user["sub"],
        Registration.event_id == event_id
    ).first()

    if not registration:
        raise NotFoundException(
            detail="Bạn chưa đăng ký. Vui lòng sử dụng chức năng đăng ký trước."
        )

    update_data = data.model_dump(exclude_unset=True)
    update_data.pop("event_id", None)
    if data.team_id:
        team = db.query(Team).filter(Team.id == data.team_id, Team.event_id == event_id).first()
        if not team:
            raise BadRequestException(detail="Team không thuộc Event này")

    # Update các trường (chỉ update trường không None)
    for field, value in update_data.items():
        setattr(registration, field, value)

    db.commit()
    db.refresh(registration)

    return _map_registration_to_response(db, registration)


@router.post("/cancel-vehicle", status_code=status.HTTP_200_OK)
async def cancel_vehicle_route(
        request: CancelVehicleRequest,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Hủy nhu cầu xe cho một chặng cụ thể.

    ⚠️ CẢNH BÁO: Hành động này KHÔNG THỂ HOÀN TÁC và sẽ KHÔNG chạy lại Auto Allocation.

    Chức năng này chỉ giải phóng slot xe để BTC có thể phân bổ thủ công cho người khác.
    User phải tự lo phương tiện di chuyển cho chặng đã hủy.
    """
    event_id = current_user.get("active_event_id")
    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện đang hoạt động")

    registration = db.query(Registration).filter(
        Registration.user_id == current_user["sub"],
        Registration.event_id == event_id
    ).first()

    if not registration:
        raise NotFoundException(detail="Bạn chưa có thông tin đăng ký")

    # Validate route_number
    if request.route_number not in [1, 2, 3, 4]:
        raise BadRequestException(detail="Chặng xe không hợp lệ. Chỉ chấp nhận 1, 2, 3, hoặc 4.")

    # Hủy nhu cầu xe (set need = False và clear assigned vehicle)
    if request.route_number == 1:
        registration.need_vehicle_route_1 = False
        registration.assigned_vehicle_1_id = None
    elif request.route_number == 2:
        registration.need_vehicle_route_2 = False
        registration.assigned_vehicle_2_id = None
    elif request.route_number == 3:
        registration.need_vehicle_route_3 = False
        registration.assigned_vehicle_3_id = None
    elif request.route_number == 4:
        registration.need_vehicle_route_4 = False
        registration.assigned_vehicle_4_id = None

    db.commit()

    return {
        "success": True,
        "message": f"Đã hủy nhu cầu xe chặng {request.route_number}. Bạn cần tự lo phương tiện di chuyển.",
        "warning": "Hành động này không thể hoàn tác và hệ thống sẽ không tự động phân bổ lại."
    }


def _map_registration_to_response(db: Session, registration: Registration) -> RegistrationResponse:
    """
    Helper function để map Registration model sang RegistrationResponse schema.
    Bao gồm thông tin flight code và vehicle names đã được phân bổ.
    """
    # Lấy flight code nếu đã phân bổ
    allocated_flight_code = None
    if registration.assigned_flight_id:
        from app.db.models.resource import Flight
        flight = db.query(Flight).filter(Flight.id == registration.assigned_flight_id).first()
        if flight:
            allocated_flight_code = flight.flight_code

    return RegistrationResponse(
        id=registration.id,
        user_id=registration.user_id,
        event_id=registration.event_id,
        team_id=registration.team_id,
        is_participating=registration.is_participating,
        desired_shift=registration.desired_shift,
        needs_vehicle_route_1=registration.need_vehicle_route_1,
        needs_vehicle_route_2=registration.need_vehicle_route_2,
        needs_vehicle_route_3=registration.need_vehicle_route_3,
        needs_vehicle_route_4=registration.need_vehicle_route_4,
        pickup_location_route_1=registration.pickup_location_route_1,
        pickup_location_route_4=registration.pickup_location_route_4,
        comments=registration.wishes,
        allocated_flight_id=registration.assigned_flight_id,
        allocated_flight_code=allocated_flight_code,
        allocated_vehicle_1_id=registration.assigned_vehicle_1_id,
        allocated_vehicle_2_id=registration.assigned_vehicle_2_id,
        allocated_vehicle_3_id=registration.assigned_vehicle_3_id,
        allocated_vehicle_4_id=registration.assigned_vehicle_4_id,
        hotel_room_code=registration.assigned_hotel_room
    )
