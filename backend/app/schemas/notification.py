from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class NotificationType(str):
    INFO = "INFO"
    WARNING = "WARNING"
    URGENT = "URGENT"


class NotificationCreate(BaseModel):
    """Request tạo thông báo mới"""
    event_id: str = Field(..., description="Event UUID")

    target_user_id: Optional[str] = Field(
        None,
        description="Gửi cho 1 user cụ thể (None = gửi cho toàn bộ)"
    )

    target_team_id: Optional[str] = Field(
        None,
        description="Gửi cho 1 Team cụ thể"
    )

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)

    notification_type: str = Field(
        default="INFO",
        description="INFO, WARNING, URGENT"
    )

    send_email: bool = Field(
        default=False,
        description="Có gửi email không"
    )

    @field_validator("notification_type")
    @classmethod
    def validate_type(cls, value):
        valid_types = ["INFO", "WARNING", "URGENT"]
        if value not in valid_types:
            raise ValueError(f"notification_type phải là một trong: {valid_types}")
        return value


class NotificationResponse(BaseModel):
    """Response thông báo"""
    id: str
    event_id: str

    target_user_id: Optional[str] = None
    target_team_id: Optional[str] = None

    title: str
    content: str
    notification_type: str

    created_by: str
    created_by_name: Optional[str] = None
    created_at: datetime

    total_recipients: int = Field(
        default=0,
        description="Tổng số người nhận"
    )
    total_read: int = Field(
        default=0,
        description="Số người đã đọc"
    )

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """Danh sách thông báo cho admin"""
    notifications: List[NotificationResponse]
    total: int
    page: int
    page_size: int


class EmailTemplate(BaseModel):
    """Template email"""
    template_type: str = Field(
        ...,
        description="registration_success, info_published, flight_change, etc."
    )
    subject: str
    body_html: str
    body_text: str
