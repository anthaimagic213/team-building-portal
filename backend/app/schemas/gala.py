from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SeatStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    LOCKING = "LOCKING"
    CONFIRMED = "CONFIRMED"
    UNAVAILABLE = "UNAVAILABLE"


class GalaTurnStatus(str, Enum):
    WAITING = "WAITING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


class GalaConfigCreate(BaseModel):
    event_id: str = Field(..., description="Event UUID")
    is_enabled: bool = Field(
        default=False,
        description="Bật hoặc tắt chức năng chọn ghế Gala",
    )
    lock_duration_seconds: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="Thời gian giữ ghế tạm thời",
    )
    turn_duration_seconds: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="Thời gian mỗi lượt Team",
    )
    rows: int = Field(default=0, ge=0, le=100)
    columns: int = Field(default=0, ge=0, le=100)


class GalaConfigUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    lock_duration_seconds: Optional[int] = Field(
        default=None,
        ge=30,
        le=3600,
    )
    turn_duration_seconds: Optional[int] = Field(
        default=None,
        ge=30,
        le=3600,
    )
    rows: Optional[int] = Field(default=None, ge=0, le=100)
    columns: Optional[int] = Field(default=None, ge=0, le=100)


class GalaConfigResponse(BaseModel):
    id: str
    event_id: str
    is_enabled: bool
    lock_duration_seconds: int
    turn_duration_seconds: int
    turn_status: GalaTurnStatus
    current_turn_number: Optional[int] = None
    turn_started_at: Optional[datetime] = None
    rows: int = 0
    columns: int = 0

    model_config = {
        "from_attributes": True,
    }


class GalaSeatCreate(BaseModel):
    event_id: str
    seat_code: str = Field(..., min_length=1, max_length=50)
    table_code: Optional[str] = Field(default=None, max_length=50)
    seat_position: Optional[int] = Field(default=None, ge=1)
    status: SeatStatus = SeatStatus.AVAILABLE


class GalaSeatUpdate(BaseModel):
    table_code: Optional[str] = Field(default=None, max_length=50)
    seat_position: Optional[int] = Field(default=None, ge=1)
    status: Optional[SeatStatus] = None


class GalaSeatResponse(BaseModel):
    id: str
    event_id: str
    seat_code: str
    table_code: Optional[str] = None
    seat_position: Optional[int] = None
    status: SeatStatus
    locked_by_team_id: Optional[str] = None
    locked_by_user_id: Optional[str] = None
    locked_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
    }


class SeatLockRequest(BaseModel):
    """
    User không gửi team_id.
    Backend lấy team_id từ JWT và kiểm tra lại với database.
    """

    seat_codes: list[str] = Field(
        ...,
        min_length=1,
        description="Danh sách mã ghế cần khóa",
    )

    @field_validator("seat_codes")
    @classmethod
    def validate_unique_seat_codes(cls, value):
        normalized = [seat.strip().upper() for seat in value if seat.strip()]

        if not normalized:
            raise ValueError("Danh sách ghế không được rỗng")

        if len(normalized) != len(set(normalized)):
            raise ValueError("Danh sách ghế không được chứa mã trùng nhau")

        return normalized


class SeatConfirmRequest(BaseModel):
    seat_codes: list[str] = Field(
        ...,
        min_length=1,
        description="Danh sách mã ghế cần xác nhận",
    )

    @field_validator("seat_codes")
    @classmethod
    def validate_unique_seat_codes(cls, value):
        normalized = [seat.strip().upper() for seat in value if seat.strip()]

        if not normalized:
            raise ValueError("Danh sách ghế không được rỗng")

        if len(normalized) != len(set(normalized)):
            raise ValueError("Danh sách ghế không được chứa mã trùng nhau")

        return normalized


class SeatReleaseRequest(BaseModel):
    seat_codes: list[str] = Field(
        ...,
        min_length=1,
        description="Danh sách ghế cần nhả lock",
    )


class GalaSeatingLayout(BaseModel):
    event_id: str
    seats: list[GalaSeatResponse]

    total_seats: int
    available_seats: int
    locked_seats: int
    confirmed_seats: int
    unavailable_seats: int

    stage_position: str = "NORTH"


class GalaTeamTurnResponse(BaseModel):
    id: str
    event_id: str
    team_id: str
    team_name: Optional[str] = None
    turn_number: int
    status: GalaTurnStatus
    valid_member_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
    }
