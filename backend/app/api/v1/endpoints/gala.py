from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.exceptions import NotFoundException
from app.db.models.user import User
from app.db.models.event import Event
from app.db.models.register import Registration
from app.db.models.representative import EventRepresentative
from app.db.session import get_db
from app.schemas.gala import (
    GalaSeatingLayout,
    SeatConfirmRequest,
    SeatLockRequest,
    SeatReleaseRequest,
)
from app.services import gala_svc
from app.services import audit_svc


router = APIRouter()


def get_event_id_from_token(current_user: dict, event_id: str | None = None) -> str:
    if event_id:
        return event_id
    event_id = current_user.get("active_event_id")

    if not event_id:
        raise NotFoundException(
            detail="Token chưa có active_event_id"
        )

    return event_id


def get_authenticated_team_member(
    current_user: dict,
    db: Session,
    event_id: str,
) -> User:
    """
    Kiểm tra người gọi API có phải đại diện Team hay không.

    Không tin team_id do request gửi lên.
    team_id được lấy từ JWT và đối chiếu với database.
    """

    user_id = current_user.get("sub")
    if not user_id:
        raise NotFoundException(
            detail="Token không có thông tin user"
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise NotFoundException(
            detail="Không tìm thấy user"
        )

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event or event.status in ("DRAFT", "REGISTRATION_OPEN"):
        from app.core.exceptions import ConflictException

        raise ConflictException(
            detail="Chỉ được đăng ký ghế Gala sau khi Event đã đóng đăng ký"
        )

    registration = db.query(Registration).filter(
        Registration.user_id == user_id,
        Registration.event_id == event_id,
        Registration.is_participating.is_(True),
    ).first()
    team_id = registration.team_id if registration else None
    if not team_id:
        from app.core.exceptions import ConflictException

        raise ConflictException(
            detail="Representative chưa được gán Team hợp lệ"
        )

    user._event_team_id = team_id
    return user


@router.get(
    "/{event_id}/seats",
    response_model=GalaSeatingLayout,
)
def get_seats(
    event_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enter the seat-selection screen for the currently active team only."""

    event_id = get_event_id_from_token(current_user, event_id)

    roles = current_user.get("roles") or []
    is_admin = "ADMIN" in roles or "SUPER_ADMIN" in roles
    if not is_admin:
        representative = get_authenticated_team_member(
            current_user=current_user,
            db=db,
            event_id=event_id,
        )

        # Viewing the interactive layout is itself entering the active turn.
        # This prevents a non-representative or a representative of another
        # team's turn from opening the seat-selection screen.
        gala_svc.release_expired_locks(db, event_id)
        gala_svc.validate_active_turn(
            db=db,
            event_id=event_id,
            team_id=representative._event_team_id,
        )

    return gala_svc.get_layout(
        db=db,
        event_id=event_id,
    )


@router.post("/{event_id}/lock")
def lock_seats(
    event_id: str,
    data: SeatLockRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Chỉ representative mới được lock ghế.

    Không nhận team_id từ body.
    """

    event_id = get_event_id_from_token(current_user, event_id)

    representative = get_authenticated_team_member(
        current_user=current_user,
        db=db,
        event_id=event_id,
    )

    gala_svc.release_expired_locks(db, event_id)

    gala_svc.validate_active_turn(
        db=db,
        event_id=event_id,
        team_id=representative._event_team_id,
    )

    gala_svc.lock_seats(
        db=db,
        event_id=event_id,
        team_id=representative._event_team_id,
        user_id=representative.id,
        seat_codes=data.seat_codes,
    )

    audit_svc.log_action(
        db=db,
        user_id=representative.id,
        emp_code=representative.emp_code,
        action="LOCK",
        entity_type="GALA_SEAT",
        entity_id=event_id,
        new_data={
            "team_id": representative._event_team_id,
            "seat_codes": data.seat_codes,
        },
        reason="Representative lock ghế Gala Dinner",
        ip_address=(
            request.client.host
            if request.client
            else None
        ),
        user_agent=request.headers.get("User-Agent"),
    )

    return {
        "success": True,
        "event_id": event_id,
        "team_id": representative._event_team_id,
        "seat_codes": data.seat_codes,
        "message": "Đã khóa ghế tạm thời",
    }


@router.post("/{event_id}/confirm")
def confirm_seats(
    event_id: str,
    data: SeatConfirmRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Chỉ representative mới được confirm ghế.
    """

    event_id = get_event_id_from_token(current_user, event_id)

    representative = get_authenticated_team_member(
        current_user=current_user,
        db=db,
        event_id=event_id,
    )

    gala_svc.confirm_seats(
        db=db,
        event_id=event_id,
        team_id=representative._event_team_id,
        user_id=representative.id,
        seat_codes=data.seat_codes,
    )

    audit_svc.log_action(
        db=db,
        user_id=representative.id,
        emp_code=representative.emp_code,
        action="CONFIRM",
        entity_type="GALA_SEAT",
        entity_id=event_id,
        new_data={
            "team_id": representative._event_team_id,
            "seat_codes": data.seat_codes,
        },
        reason="Representative xác nhận ghế Gala Dinner",
        ip_address=(
            request.client.host
            if request.client
            else None
        ),
        user_agent=request.headers.get("User-Agent"),
    )

    return {
        "success": True,
        "event_id": event_id,
        "team_id": representative._event_team_id,
        "seat_codes": data.seat_codes,
        "message": "Đã xác nhận ghế chính thức",
    }


@router.post("/{event_id}/release")
def release_seats(
    event_id: str,
    data: SeatReleaseRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Representative chỉ được nhả các ghế LOCKING
    của chính Team mình.
    """

    event_id = get_event_id_from_token(current_user, event_id)

    representative = get_authenticated_team_member(
        current_user=current_user,
        db=db,
        event_id=event_id,
    )

    released_count = gala_svc.release_seats(
        db=db,
        event_id=event_id,
        team_id=representative._event_team_id,
        user_id=representative.id,
        seat_codes=data.seat_codes,
    )

    audit_svc.log_action(
        db=db,
        user_id=representative.id,
        emp_code=representative.emp_code,
        action="RELEASE",
        entity_type="GALA_SEAT",
        entity_id=event_id,
        old_data={
            "team_id": representative._event_team_id,
            "seat_codes": data.seat_codes,
        },
        new_data={
            "released_count": released_count,
        },
        reason="Representative nhả ghế đang lock",
        ip_address=(
            request.client.host
            if request.client
            else None
        ),
        user_agent=request.headers.get("User-Agent"),
    )

    return {
        "success": True,
        "released_count": released_count,
        "message": "Đã nhả ghế đang giữ",
    }
