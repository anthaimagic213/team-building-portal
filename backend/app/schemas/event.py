from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class EventStatus(str, Enum):
    """
    Event status cho quản lý vòng đời sự kiện.

    State Machine:
    DRAFT → REGISTRATION_OPEN → REGISTRATION_CLOSED →
    ALLOCATION_IN_PROGRESS → ALLOCATION_COMPLETED →
    EVENT_ACTIVE → EVENT_COMPLETED
    """
    DRAFT = "DRAFT"
    REGISTRATION_OPEN = "REGISTRATION_OPEN"
    REGISTRATION_CLOSED = "REGISTRATION_CLOSED"
    ALLOCATION_IN_PROGRESS = "ALLOCATION_IN_PROGRESS"
    ALLOCATION_COMPLETED = "ALLOCATION_COMPLETED"
    EVENT_ACTIVE = "EVENT_ACTIVE"
    EVENT_COMPLETED = "EVENT_COMPLETED"


class EventBase(BaseModel):
    """Base schema for Event"""
    event_name: str = Field(..., description="Tên sự kiện (VD: Team Building Da Nang 2026)")
    event_date_start: datetime = Field(..., description="Ngày bắt đầu sự kiện")
    event_date_end: datetime = Field(..., description="Ngày kết thúc sự kiện")
    location: str = Field(..., description="Địa điểm (VD: Da Nang, Phu Quoc)")
    registration_deadline: datetime = Field(..., description="Deadline đăng ký")
    description: str | None = Field(None, description="Mô tả chi tiết sự kiện")


class EventCreate(EventBase):
    """Schema for creating a new event"""
    pass


class EventUpdate(BaseModel):
    """Schema for updating event information"""
    event_name: str | None = None
    event_date_start: datetime | None = None
    event_date_end: datetime | None = None
    location: str | None = None
    registration_deadline: datetime | None = None
    description: str | None = None
    status: EventStatus | None = None


class EventResponse(EventBase):
    """
    Event response with full details.

    Dùng cho:
    - Admin xem danh sách events
    - User kiểm tra event nào đang active
    """
    id: str = Field(..., description="Event UUID")
    status: EventStatus = Field(..., description="Trạng thái hiện tại")
    total_participants: int = Field(default=0, description="Số người đã đăng ký tham gia")
    created_at: datetime

    class Config:
        from_attributes = True
