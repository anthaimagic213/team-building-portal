from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import require_admin_role
from app.core.exceptions import BadRequestException, NotFoundException
from app.db.models.event import Event
from app.db.models.gala import GalaSeat
from app.db.session import get_db
from app.schemas.gala import (
    GalaConfigCreate,
    GalaConfigResponse,
    GalaConfigUpdate,
    GalaSeatCreate,
    GalaSeatResponse,
    GalaSeatUpdate,
    GalaTeamTurnResponse,
)
from app.services import gala_svc


router = APIRouter()


def validate_event(
    db: Session,
    event_id: str,
) -> Event:
    event = (
        db.query(Event)
        .filter(Event.id == event_id)
        .first()
    )

    if not event:
        raise NotFoundException(
            detail="Không tìm thấy Event"
        )

    return event


@router.get(
    "/config/{event_id}",
    response_model=GalaConfigResponse,
)
def get_config(
    event_id: str,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db),
):
    validate_event(db, event_id)

    return gala_svc.get_gala_config(
        db=db,
        event_id=event_id,
    )


@router.post(
    "/config",
    response_model=GalaConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_config(
    data: GalaConfigCreate,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db),
):
    validate_event(db, data.event_id)

    config = gala_svc.create_or_update_config(
        db=db,
        event_id=data.event_id,
        is_enabled=data.is_enabled,
        lock_duration_seconds=data.lock_duration_seconds,
        turn_duration_seconds=data.turn_duration_seconds,
        rows=data.rows,
        columns=data.columns,
    )

    return config


@router.put(
    "/config/{event_id}",
    response_model=GalaConfigResponse,
)
def update_config(
    event_id: str,
    data: GalaConfigUpdate,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db),
):
    config = gala_svc.get_gala_config(
        db=db,
        event_id=event_id,
    )

    if data.is_enabled is not None:
        config.is_enabled = data.is_enabled

    if data.lock_duration_seconds is not None:
        config.lock_duration_seconds = data.lock_duration_seconds

    if data.turn_duration_seconds is not None:
        config.turn_duration_seconds = data.turn_duration_seconds

    if data.rows is not None:
        config.rows = data.rows
    if data.columns is not None:
        config.columns = data.columns

    db.commit()
    db.refresh(config)

    return config


@router.post("/layout/{event_id}", response_model=GalaConfigResponse)
def generate_layout(
    event_id: str,
    rows: int,
    columns: int,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db),
):
    validate_event(db, event_id)
    if rows < 1 or columns < 1:
        raise BadRequestException(detail="Số hàng và số cột phải lớn hơn 0")
    config = gala_svc.get_gala_config(db=db, event_id=event_id)
    existing = db.query(GalaSeat).filter(GalaSeat.event_id == event_id).count()
    if existing:
        raise BadRequestException(detail="Event đã có layout ghế; không thể tạo lại")
    config.rows, config.columns = rows, columns
    for row in range(rows):
        for column in range(columns):
            db.add(GalaSeat(event_id=event_id, seat_code=f"R{row + 1:02d}C{column + 1:02d}", table_code=f"R{row + 1:02d}", seat_position=column + 1, status="AVAILABLE"))
    db.commit()
    db.refresh(config)
    return config


@router.post(
    "/seats",
    response_model=GalaSeatResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_seat(
    data: GalaSeatCreate,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db),
):
    validate_event(db, data.event_id)

    existing = (
        db.query(GalaSeat)
        .filter(
            GalaSeat.event_id == data.event_id,
            GalaSeat.seat_code == data.seat_code.upper(),
        )
        .first()
    )

    if existing:
        raise BadRequestException(
            detail="Mã ghế đã tồn tại trong Event"
        )

    seat = GalaSeat(
        event_id=data.event_id,
        seat_code=data.seat_code.upper(),
        table_code=data.table_code,
        seat_position=data.seat_position,
        status=data.status.value,
    )

    db.add(seat)
    db.commit()
    db.refresh(seat)

    return seat


@router.put(
    "/seats/{seat_id}",
    response_model=GalaSeatResponse,
)
def update_seat(
    seat_id: str,
    data: GalaSeatUpdate,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db),
):
    seat = (
        db.query(GalaSeat)
        .filter(GalaSeat.id == seat_id)
        .first()
    )

    if not seat:
        raise NotFoundException(
            detail="Không tìm thấy ghế"
        )

    if seat.status in {"LOCKING", "CONFIRMED"}:
        raise BadRequestException(
            detail=(
                "Không thể chỉnh sửa ghế đang LOCKING "
                "hoặc đã CONFIRMED"
            )
        )

    if data.table_code is not None:
        seat.table_code = data.table_code

    if data.seat_position is not None:
        seat.seat_position = data.seat_position

    if data.status is not None:
        seat.status = data.status.value

    db.commit()
    db.refresh(seat)

    return seat


@router.delete(
    "/seats/{seat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_seat(
    seat_id: str,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db),
):
    seat = (
        db.query(GalaSeat)
        .filter(GalaSeat.id == seat_id)
        .first()
    )

    if not seat:
        raise NotFoundException(
            detail="Không tìm thấy ghế"
        )

    if seat.status in {"LOCKING", "CONFIRMED"}:
        raise BadRequestException(
            detail=(
                "Không thể xóa ghế đang LOCKING "
                "hoặc đã CONFIRMED"
            )
        )

    db.delete(seat)
    db.commit()

    return None


@router.post(
    "/turns/randomize/{event_id}",
    response_model=list[GalaTeamTurnResponse],
)
def randomize_turns(
    event_id: str,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db),
):
    validate_event(db, event_id)

    gala_svc.get_gala_config(
        db=db,
        event_id=event_id,
    )

    turns = gala_svc.randomize_team_turns(
        db=db,
        event_id=event_id,
    )

    return gala_svc.get_team_turns(
        db=db,
        event_id=event_id,
    )


@router.post(
    "/turns/next/{event_id}",
    response_model=GalaTeamTurnResponse,
)
def activate_next_turn(
    event_id: str,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db),
):
    validate_event(db, event_id)

    turn = gala_svc.activate_next_turn(
        db=db,
        event_id=event_id,
    )

    result = gala_svc.get_team_turns(
        db=db,
        event_id=event_id,
    )

    for item in result:
        if item.id == turn.id:
            return item

    raise NotFoundException(
        detail="Không tìm thấy lượt vừa được kích hoạt"
    )


@router.get(
    "/turns/{event_id}",
    response_model=list[GalaTeamTurnResponse],
)
def list_turns(
    event_id: str,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db),
):
    validate_event(db, event_id)

    return gala_svc.get_team_turns(
        db=db,
        event_id=event_id,
    )
