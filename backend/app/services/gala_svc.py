from datetime import datetime, timedelta
from random import shuffle
from typing import Optional

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.db.models.gala import GalaConfig, GalaSeat, GalaTeamTurn
from app.db.models.representative import EventRepresentative
from app.db.models.register import Registration
from app.db.models.user import Team, User
from app.schemas.gala import (
    GalaConfigResponse,
    GalaSeatResponse,
    GalaSeatingLayout,
    GalaTeamTurnResponse,
)


VALID_ROUTE_STATUSES = {
    "AVAILABLE",
    "LOCKING",
    "CONFIRMED",
    "UNAVAILABLE",
}


def get_gala_config(
    db: Session,
    event_id: str,
) -> GalaConfig:
    config = (
        db.query(GalaConfig)
        .filter(GalaConfig.event_id == event_id)
        .first()
    )

    if not config:
        raise NotFoundException(
            detail="Event chưa có cấu hình Gala Dinner"
        )

    return config


def create_or_update_config(
    db: Session,
    event_id: str,
    is_enabled: bool,
    lock_duration_seconds: int,
    turn_duration_seconds: int,
    rows: int = 0,
    columns: int = 0,
) -> GalaConfig:
    config = (
        db.query(GalaConfig)
        .filter(GalaConfig.event_id == event_id)
        .first()
    )

    if not config:
        config = GalaConfig(
            event_id=event_id,
            is_enabled=is_enabled,
            lock_duration_seconds=lock_duration_seconds,
            turn_duration_seconds=turn_duration_seconds,
            turn_status="WAITING",
            rows=rows,
            columns=columns,
        )
        db.add(config)
    else:
        config.is_enabled = is_enabled
        config.lock_duration_seconds = lock_duration_seconds
        config.turn_duration_seconds = turn_duration_seconds
        config.rows = rows
        config.columns = columns

    db.commit()
    db.refresh(config)

    return config


def release_expired_locks(
    db: Session,
    event_id: str,
) -> int:
    """
    Tự động giải phóng các ghế LOCKING đã quá thời hạn.

    Hàm này được gọi trước khi:
    - Trả layout ghế
    - Lock ghế
    - Confirm ghế
    """

    config = (
        db.query(GalaConfig)
        .filter(GalaConfig.event_id == event_id)
        .first()
    )

    if not config:
        return 0

    expired_before = datetime.utcnow() - timedelta(
        seconds=config.lock_duration_seconds
    )

    result = (
        db.query(GalaSeat)
        .filter(
            GalaSeat.event_id == event_id,
            GalaSeat.status == "LOCKING",
            GalaSeat.locked_at.isnot(None),
            GalaSeat.locked_at < expired_before,
        )
        .update(
            {
                "status": "AVAILABLE",
                "locked_by_team_id": None,
                "locked_by_user_id": None,
                "locked_at": None,
            },
            synchronize_session=False,
        )
    )

    db.commit()

    return result


def get_layout(
    db: Session,
    event_id: str,
) -> GalaSeatingLayout:
    release_expired_locks(db, event_id)

    seats = (
        db.query(GalaSeat)
        .filter(GalaSeat.event_id == event_id)
        .order_by(
            GalaSeat.table_code.asc(),
            GalaSeat.seat_position.asc(),
            GalaSeat.seat_code.asc(),
        )
        .all()
    )

    available_count = sum(
        1 for seat in seats if seat.status == "AVAILABLE"
    )
    locking_count = sum(
        1 for seat in seats if seat.status == "LOCKING"
    )
    confirmed_count = sum(
        1 for seat in seats if seat.status == "CONFIRMED"
    )
    unavailable_count = sum(
        1 for seat in seats if seat.status == "UNAVAILABLE"
    )

    return GalaSeatingLayout(
        event_id=event_id,
        seats=[
            GalaSeatResponse.model_validate(seat)
            for seat in seats
        ],
        total_seats=len(seats),
        available_seats=available_count,
        locked_seats=locking_count,
        confirmed_seats=confirmed_count,
        unavailable_seats=unavailable_count,
    )


def get_valid_team_member_count(
    db: Session,
    event_id: str,
    team_id: str,
) -> int:
    """
    Thành viên hợp lệ là:
    - Thuộc đúng Team
    - Có registration trong Event
    - is_participating = True
    """

    return (
        db.query(Registration)
        .join(User, User.id == Registration.user_id)
        .filter(
            Registration.event_id == event_id,
            Registration.is_participating.is_(True),
            Registration.team_id == team_id,
        )
        .count()
    )


def validate_team_representative(
    db: Session,
    event_id: str,
    team_id: Optional[str],
    user_id: Optional[str],
) -> str:
    """
    Chỉ user có is_representative = True mới được chọn ghế.

    Đồng thời user phải:
    - Có team_id
    - Thuộc một Team của Event hiện tại
    - Có registration tham gia Event
    """

    if not team_id:
        raise BadRequestException(
            detail="User chưa được gán vào Team"
        )

    if not user_id:
        raise BadRequestException(
            detail="Token không chứa user_id"
        )

    representative = (
        db.query(User)
        .join(Registration, Registration.user_id == User.id)
        .join(Team, Team.id == Registration.team_id)
        .join(EventRepresentative, EventRepresentative.user_id == User.id)
        .filter(
            User.id == user_id,
            Registration.team_id == team_id,
            Registration.event_id == event_id,
            Registration.is_participating.is_(True),
            EventRepresentative.event_id == event_id,
            EventRepresentative.team_id == team_id,
            Team.event_id == event_id,
        )
        .first()
    )

    if not representative:
        raise ConflictException(
            detail=(
                "Chỉ người được chỉ định là đại diện Team "
                "mới được đăng ký hoặc chọn ghế Gala Dinner"
            )
        )

    representative_registration = (
        db.query(Registration)
        .filter(
            Registration.user_id == user_id,
            Registration.event_id == event_id,
            Registration.is_participating.is_(True),
        )
        .first()
    )

    if not representative_registration:
        raise ConflictException(
            detail=(
                "Đại diện Team chưa có đăng ký tham gia "
                "Event này"
            )
        )

    return team_id


def validate_active_turn(
    db: Session,
    event_id: str,
    team_id: str,
) -> GalaTeamTurn:
    config = get_gala_config(db, event_id)

    if not config.is_enabled:
        raise BadRequestException(
            detail="Gala Dinner hiện chưa được mở"
        )

    if config.turn_status != "ACTIVE":
        raise BadRequestException(
            detail="Gala Dinner hiện chưa có lượt chọn ghế đang hoạt động"
        )

    current_turn = (
        db.query(GalaTeamTurn)
        .filter(
            GalaTeamTurn.event_id == event_id,
            GalaTeamTurn.team_id == team_id,
            GalaTeamTurn.status == "ACTIVE",
            GalaTeamTurn.turn_number == config.current_turn_number,
        )
        .first()
    )

    if not current_turn:
        raise ConflictException(
            detail="Team của bạn chưa đến lượt chọn ghế"
        )

    if current_turn.started_at:
        turn_expired_at = current_turn.started_at + timedelta(
            seconds=config.turn_duration_seconds
        )

        if datetime.utcnow() > turn_expired_at:
            current_turn.status = "SKIPPED"
            current_turn.completed_at = datetime.utcnow()
            db.commit()

            raise ConflictException(
                detail="Lượt chọn ghế của Team đã hết thời gian"
            )

    return current_turn


def validate_requested_seat_count(
    db: Session,
    event_id: str,
    team_id: str,
    seat_codes: list[str],
) -> None:
    valid_member_count = get_valid_team_member_count(
        db=db,
        event_id=event_id,
        team_id=team_id,
    )

    if valid_member_count <= 0:
        raise BadRequestException(
            detail="Team không có thành viên hợp lệ tham gia Event"
        )

    if len(seat_codes) > valid_member_count:
        raise BadRequestException(
            detail=(
                f"Team có {valid_member_count} thành viên hợp lệ, "
                f"không thể chọn {len(seat_codes)} ghế"
            )
        )


def lock_seats(
    db: Session,
    event_id: str,
    team_id: str,
    user_id: str,
    seat_codes: list[str],
) -> None:
    """
    Lock ghế bằng UPDATE có điều kiện.

    Điều kiện quan trọng:
    - Đúng Event
    - status = AVAILABLE

    Nếu một ghế vừa bị Team khác lấy trước đó,
    rowcount sẽ nhỏ hơn số ghế yêu cầu và toàn bộ transaction rollback.
    """

    seat_codes = list(dict.fromkeys(
        code.strip().upper()
        for code in seat_codes
    ))

    if len(seat_codes) != 1:
        raise BadRequestException(detail="Mỗi thành viên chỉ được chọn đúng 1 ghế")
    if not seat_codes:
        raise BadRequestException(
            detail="Danh sách ghế không được rỗng"
        )

    validate_requested_seat_count(
        db=db,
        event_id=event_id,
        team_id=team_id,
        seat_codes=seat_codes,
    )

    # Một user chỉ được giữ một ghế trong Event.
    existing_locked_count = (
        db.query(GalaSeat)
        .filter(
            GalaSeat.event_id == event_id,
            GalaSeat.locked_by_user_id == user_id,
            GalaSeat.status == "LOCKING",
        )
        .count()
    )

    if existing_locked_count + len(seat_codes) > 1:
        raise BadRequestException(
            detail=(
                f"Team chỉ được chọn tối đa "
                f"{valid_member_count} ghế"
            )
        )

    requested_seats = (
        db.query(GalaSeat)
        .filter(
            GalaSeat.event_id == event_id,
            GalaSeat.seat_code.in_(seat_codes),
        )
        .all()
    )

    if len(requested_seats) != len(seat_codes):
        found_codes = {seat.seat_code for seat in requested_seats}
        missing_codes = [
            code for code in seat_codes
            if code not in found_codes
        ]

        raise NotFoundException(
            detail=f"Không tìm thấy ghế: {missing_codes}"
        )

    now = datetime.utcnow()

    stmt = (
        update(GalaSeat)
        .where(
            GalaSeat.event_id == event_id,
            GalaSeat.seat_code.in_(seat_codes),
            GalaSeat.status == "AVAILABLE",
        )
        .values(
            status="LOCKING",
            locked_by_team_id=team_id,
            locked_by_user_id=user_id,
            locked_at=now,
        )
    )

    result = db.execute(stmt)

    if result.rowcount != len(seat_codes):
        db.rollback()

        raise ConflictException(
            detail=(
                "Một hoặc nhiều ghế vừa được Team khác "
                "chọn trước. Vui lòng tải lại sơ đồ ghế."
            )
        )

    db.commit()


def confirm_seats(
    db: Session,
    event_id: str,
    team_id: str,
    user_id: str,
    seat_codes: list[str],
) -> None:
    """
    Chuyển ghế LOCKING của chính Team thành CONFIRMED.
    """

    seat_codes = list(dict.fromkeys(
        code.strip().upper()
        for code in seat_codes
    ))

    if not seat_codes:
        raise BadRequestException(
            detail="Danh sách ghế không được rỗng"
        )

    release_expired_locks(db, event_id)

    config = get_gala_config(db, event_id)

    locked_before = datetime.utcnow() - timedelta(
        seconds=config.lock_duration_seconds
    )

    stmt = (
        update(GalaSeat)
        .where(
            GalaSeat.event_id == event_id,
            GalaSeat.seat_code.in_(seat_codes),
            GalaSeat.status == "LOCKING",
            GalaSeat.locked_by_team_id == team_id,
            GalaSeat.locked_by_user_id == user_id,
            GalaSeat.locked_at >= locked_before,
        )
        .values(status="CONFIRMED")
    )

    result = db.execute(stmt)

    if result.rowcount != len(seat_codes):
        db.rollback()

        raise ConflictException(
            detail=(
                "Ghế đã hết thời gian giữ hoặc không thuộc "
                "quyền giữ của Team này"
            )
        )

    current_turn = (
        db.query(GalaTeamTurn)
        .filter(
            GalaTeamTurn.event_id == event_id,
            GalaTeamTurn.team_id == team_id,
            GalaTeamTurn.status == "ACTIVE",
        )
        .first()
    )

    confirmed_count = db.query(GalaSeat).filter(
        GalaSeat.event_id == event_id,
        GalaSeat.locked_by_team_id == team_id,
        GalaSeat.status == "CONFIRMED",
    ).count()
    if current_turn and confirmed_count >= get_valid_team_member_count(db, event_id, team_id):
        current_turn.status = "COMPLETED"
        current_turn.completed_at = datetime.utcnow()

    db.commit()


def release_seats(
    db: Session,
    event_id: str,
    team_id: str,
    user_id: str,
    seat_codes: list[str],
) -> int:
    """
    Chỉ nhả được ghế LOCKING của chính Team.
    Không được nhả ghế CONFIRMED.
    """

    seat_codes = list(dict.fromkeys(
        code.strip().upper()
        for code in seat_codes
    ))

    result = (
        db.query(GalaSeat)
        .filter(
            GalaSeat.event_id == event_id,
            GalaSeat.seat_code.in_(seat_codes),
            GalaSeat.status == "LOCKING",
            GalaSeat.locked_by_team_id == team_id,
            GalaSeat.locked_by_user_id == user_id,
        )
        .update(
            {
                "status": "AVAILABLE",
                "locked_by_team_id": None,
                "locked_by_user_id": None,
                "locked_at": None,
            },
            synchronize_session=False,
        )
    )

    db.commit()

    return result


def randomize_team_turns(
    db: Session,
    event_id: str,
) -> list[GalaTeamTurn]:
    """
    Random thứ tự các Team có ít nhất một thành viên hợp lệ.
    """

    teams = (
        db.query(Team)
        .filter(Team.event_id == event_id)
        .all()
    )

    eligible_teams = []

    for team in teams:
        member_count = get_valid_team_member_count(
            db=db,
            event_id=event_id,
            team_id=team.id,
        )

        if member_count > 0:
            eligible_teams.append(team)

    if not eligible_teams:
        raise BadRequestException(
            detail="Không có Team nào có thành viên hợp lệ"
        )

    shuffle(eligible_teams)

    # Xóa thứ tự cũ
    db.query(GalaTeamTurn).filter(
        GalaTeamTurn.event_id == event_id
    ).delete(
        synchronize_session=False
    )

    turns = []

    for index, team in enumerate(eligible_teams, start=1):
        turn = GalaTeamTurn(
            event_id=event_id,
            team_id=team.id,
            turn_number=index,
            status="WAITING",
        )
        db.add(turn)
        turns.append(turn)

    config = get_gala_config(db, event_id)
    config.turn_status = "WAITING"
    config.current_turn_number = None
    config.turn_started_at = None

    db.commit()

    for turn in turns:
        db.refresh(turn)

    return turns


def activate_next_turn(
    db: Session,
    event_id: str,
) -> GalaTeamTurn:
    config = get_gala_config(db, event_id)

    current_active = (
        db.query(GalaTeamTurn)
        .filter(
            GalaTeamTurn.event_id == event_id,
            GalaTeamTurn.status == "ACTIVE",
        )
        .first()
    )

    if current_active:
        raise ConflictException(
            detail=(
                f"Team hiện tại vẫn đang ở lượt "
                f"{current_active.turn_number}"
            )
        )

    next_turn = (
        db.query(GalaTeamTurn)
        .filter(
            GalaTeamTurn.event_id == event_id,
            GalaTeamTurn.status == "WAITING",
        )
        .order_by(GalaTeamTurn.turn_number.asc())
        .first()
    )

    if not next_turn:
        config.turn_status = "COMPLETED"
        config.current_turn_number = None
        config.turn_started_at = None
        db.commit()

        raise NotFoundException(
            detail="Không còn Team nào đang chờ lượt"
        )

    now = datetime.utcnow()

    next_turn.status = "ACTIVE"
    next_turn.started_at = now

    config.turn_status = "ACTIVE"
    config.current_turn_number = next_turn.turn_number
    config.turn_started_at = now

    db.commit()
    db.refresh(next_turn)

    return next_turn


def get_team_turns(
    db: Session,
    event_id: str,
) -> list[GalaTeamTurnResponse]:
    turns = (
        db.query(GalaTeamTurn)
        .filter(GalaTeamTurn.event_id == event_id)
        .order_by(GalaTeamTurn.turn_number.asc())
        .all()
    )

    result = []

    for turn in turns:
        team_name = turn.team.name if turn.team else None

        member_count = get_valid_team_member_count(
            db=db,
            event_id=event_id,
            team_id=turn.team_id,
        )

        result.append(
            GalaTeamTurnResponse(
                id=turn.id,
                event_id=turn.event_id,
                team_id=turn.team_id,
                team_name=team_name,
                turn_number=turn.turn_number,
                status=turn.status,
                valid_member_count=member_count,
                started_at=turn.started_at,
                completed_at=turn.completed_at,
            )
        )

    return result
