from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class JourneyFlightInfo(BaseModel):
    """Thông tin chuyến bay trong hành trình"""
    flight_code: str = Field(..., description="Mã chuyến bay (VD: VN123)")
    direction: str = Field(..., description="OUTBOUND (đi) hoặc RETURN (về)")
    departure_time: datetime = Field(..., description="Thời gian khởi hành")
    arrival_time: datetime = Field(..., description="Thời gian đến")
    origin: str = Field(..., description="Điểm đi (HAN, SGN)")
    destination: str = Field(..., description="Điểm đến (DAD, PQC)")


class JourneyVehicleInfo(BaseModel):
    """Thông tin xe trong hành trình"""
    vehicle_name: str = Field(..., description="Tên xe (Bus 01, Xe 15 chỗ A)")
    route_type: str = Field(..., description="Chặng (ROUTE_1, ROUTE_2, ROUTE_3, ROUTE_4)")
    departure_time: datetime = Field(..., description="Thời gian khởi hành")
    pickup_location: str = Field(..., description="Điểm đón")
    dropoff_location: Optional[str] = Field(None, description="Điểm trả")
    captain_name: Optional[str] = Field(None, description="Tên Trưởng xe")
    captain_phone: Optional[str] = Field(None, description="SĐT Trưởng xe")
    notes: Optional[str] = Field(None, description="Ghi chú")


class JourneyHotelInfo(BaseModel):
    """Thông tin khách sạn trong hành trình"""
    hotel_name: str = Field(..., description="Tên khách sạn")
    address: Optional[str] = Field(None, description="Địa chỉ")
    phone: Optional[str] = Field(None, description="Số điện thoại khách sạn")
    room_code: str = Field(..., description="Mã phòng (VD: A101, B205)")
    room_type: Optional[str] = Field(None, description="Loại phòng (Single, Double, Suite)")
    roommates: List[str] = Field(
        default_factory=list,
        description="Danh sách người ở cùng phòng (full_name)"
    )


class JourneyGalaInfo(BaseModel):
    """Thông tin Gala Dinner trong hành trình"""
    seat_code: str = Field(..., description="Mã ghế (VD: A1, B5)")
    table_code: Optional[str] = Field(None, description="Mã bàn (VD: TABLE_A, TABLE_B)")
    seat_position: Optional[int] = Field(None, description="Vị trí ghế trong bàn")
    status: str = Field(..., description="Trạng thái (CONFIRMED, LOCKING)")


class EventScheduleItem(BaseModel):
    """Một mục trong lịch trình sự kiện"""
    time: datetime = Field(..., description="Thời gian")
    title: str = Field(..., description="Tiêu đề hoạt động")
    description: Optional[str] = Field(None, description="Mô tả chi tiết")
    location: Optional[str] = Field(None, description="Địa điểm")


class NotificationItem(BaseModel):
    """Thông báo từ BTC"""
    id: str = Field(..., description="Notification UUID")
    title: str = Field(..., description="Tiêu đề thông báo")
    content: str = Field(..., description="Nội dung thông báo")
    notification_type: str = Field(..., description="Loại thông báo (INFO, WARNING, URGENT)")
    created_at: datetime = Field(..., description="Thời gian tạo")
    is_read: bool = Field(default=False, description="Đã đọc hay chưa")


class MyJourneyResponse(BaseModel):
    """
    Response đầy đủ cho My Journey.

    Tổng hợp toàn bộ thông tin hành trình của CBNV.
    """
    # Thông tin cá nhân
    user_name: str = Field(..., description="Họ tên CBNV")
    emp_code: str = Field(..., description="Mã nhân viên")
    email: str = Field(..., description="Email")
    phone: Optional[str] = Field(None, description="Số điện thoại")

    # Thông tin Team
    team_name: Optional[str] = Field(None, description="Tên Team/Bộ phận")
    team_leader: Optional[str] = Field(None, description="Tên trưởng Team")

    # Thông tin Event
    event_name: str = Field(..., description="Tên sự kiện")
    event_date_start: datetime = Field(..., description="Ngày bắt đầu")
    event_date_end: datetime = Field(..., description="Ngày kết thúc")
    event_location: str = Field(..., description="Địa điểm tổ chức")
    event_status: str = Field(..., description="Trạng thái sự kiện")

    # Registration status
    is_participating: bool = Field(..., description="Có tham gia hay không")
    registration_status: str = Field(
        ...,
        description="Trạng thái đăng ký (PENDING, CONFIRMED, CANCELLED)"
    )

    # Chuyến bay
    outbound_flight: Optional[JourneyFlightInfo] = Field(
        None,
        description="Chuyến bay đi"
    )
    return_flight: Optional[JourneyFlightInfo] = Field(
        None,
        description="Chuyến bay về"
    )

    # Xe 4 chặng
    vehicles: List[JourneyVehicleInfo] = Field(
        default_factory=list,
        description="Danh sách xe cho 4 chặng"
    )

    # Khách sạn
    hotel: Optional[JourneyHotelInfo] = Field(
        None,
        description="Thông tin khách sạn và phòng"
    )

    # Gala Dinner
    gala_seat: Optional[JourneyGalaInfo] = Field(
        None,
        description="Thông tin ghế Gala Dinner"
    )

    # Lịch trình
    schedule: List[EventScheduleItem] = Field(
        default_factory=list,
        description="Lịch trình tổng thể của chương trình"
    )

    # Thông báo
    notifications: List[NotificationItem] = Field(
        default_factory=list,
        description="Các thông báo/thay đổi mới nhất từ BTC"
    )

    # Metadata
    last_updated: datetime = Field(..., description="Thời điểm cập nhật cuối")


class JourneySummary(BaseModel):
    """
    Tóm tắt hành trình (dùng cho list view hoặc widget).
    """
    user_name: str
    emp_code: str
    team_name: Optional[str] = None

    has_flight: bool = Field(default=False, description="Đã có chuyến bay")
    has_vehicle: bool = Field(default=False, description="Đã có xe")
    has_hotel: bool = Field(default=False, description="Đã có phòng")
    has_gala_seat: bool = Field(default=False, description="Đã có ghế Gala")

    completion_percentage: int = Field(
        ...,
        ge=0,
        le=100,
        description="Phần trăm hoàn thành thông tin"
    )


class JourneyEventItem(BaseModel):
    id: str
    event_name: str
    event_date_start: Optional[datetime] = None
    event_date_end: Optional[datetime] = None
    location: Optional[str] = None
    registration_deadline: Optional[datetime] = None
    status: str
    teams: list[dict] = Field(default_factory=list)
    participant_count: int = 0
    can_manage_gala: bool = False
    registration: Optional[dict] = None
