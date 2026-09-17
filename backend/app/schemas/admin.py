from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EventStatistics(BaseModel):
    """Thống kê tổng quan của Event"""
    event_id: str
    event_name: str
    event_status: str

    # Thống kê đăng ký
    total_employees: int = Field(..., description="Tổng số CBNV trong hệ thống")
    total_registered: int = Field(..., description="Số người đã đăng ký")
    total_participating: int = Field(..., description="Số người tham gia (is_participating=True)")
    registration_rate: float = Field(..., description="Tỷ lệ đăng ký (%)")

    # Đăng ký theo Ca
    shift_1_count: int = Field(..., description="Số người chọn Ca 1")
    shift_2_count: int = Field(..., description="Số người chọn Ca 2")
    no_shift_preference: int = Field(..., description="Số người không chọn Ca")

    # Thống kê chuyến bay
    total_flights: int = Field(..., description="Tổng số chuyến bay")
    total_flight_slots: int = Field(..., description="Tổng số ghế trên tất cả chuyến")
    allocated_flight_slots: int = Field(..., description="Số ghế đã phân bổ")
    available_flight_slots: int = Field(..., description="Số ghế còn trống")
    flight_utilization_rate: float = Field(..., description="Tỷ lệ sử dụng ghế bay (%)")
    unallocated_flight_users: int = Field(default=0, description="Số người chưa được xếp chuyến bay")
    unallocated_flight_user_ids: List[str] = Field(default_factory=list)
    allocation_warnings: List[str] = Field(default_factory=list)

    # Thống kê xe theo chặng
    vehicle_stats_route_1: Dict[str, int] = Field(
        default_factory=dict,
        description="Thống kê xe chặng 1: {need, allocated, unallocated}"
    )
    vehicle_stats_route_2: Dict[str, int] = Field(default_factory=dict)
    vehicle_stats_route_3: Dict[str, int] = Field(default_factory=dict)
    vehicle_stats_route_4: Dict[str, int] = Field(default_factory=dict)

    # Thống kê Gala
    total_gala_seats: int = Field(..., description="Tổng số ghế Gala")
    confirmed_gala_seats: int = Field(..., description="Số ghế đã confirm")
    available_gala_seats: int = Field(..., description="Số ghế còn trống")

    # Thống kê khách sạn
    total_hotel_rooms: int = Field(..., description="Tổng số phòng khách sạn")
    total_hotel_rooms_assigned: int = Field(..., description="Số phòng đã phân bổ")

    last_updated: datetime


class TeamStatistics(BaseModel):
    """Thống kê theo Team"""
    team_id: str
    team_name: str

    total_members: int = Field(..., description="Tổng số thành viên")
    registered_members: int = Field(..., description="Số người đã đăng ký")
    participating_members: int = Field(..., description="Số người tham gia")

    allocated_flight: int = Field(..., description="Số người đã có chuyến bay")
    allocated_vehicle: int = Field(..., description="Số người đã có xe")
    allocated_hotel: int = Field(..., description="Số người đã có phòng")

    has_gala_seat: bool = Field(..., description="Team đã có ghế Gala")

    completion_rate: float = Field(..., description="Tỷ lệ hoàn thành (%)")


class UserListItem(BaseModel):
    """Item trong danh sách CBNV"""
    id: str
    emp_code: str
    full_name: str
    email: str
    phone: Optional[str] = None
    team_name: Optional[str] = None
    work_location: Optional[str] = None
    is_representative: bool = False

    is_registered: bool = Field(..., description="Đã đăng ký chưa")
    is_participating: bool = Field(default=False, description="Có tham gia không")
    desired_shift: Optional[str] = Field(None, description="Ca mong muốn")

    has_flight: bool = Field(default=False, description="Đã có chuyến bay")
    has_vehicle: bool = Field(default=False, description="Đã có xe")
    has_hotel: bool = Field(default=False, description="Đã có phòng")

    completion_percentage: int = Field(..., description="% hoàn thành")


class FlightStatistics(BaseModel):
    """Thống kê một chuyến bay"""
    flight_id: str
    flight_code: str
    direction: str
    departure_time: datetime

    total_slots: int
    assigned_count: int
    available_slots: int
    utilization_rate: float

    # Phân bổ theo Team
    team_breakdown: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Danh sách Team trên chuyến này"
    )


class VehicleStatistics(BaseModel):
    """Thống kê một xe"""
    vehicle_id: str
    vehicle_name: str
    route_type: str

    capacity: int
    assigned_count: int
    available_capacity: int
    utilization_rate: float

    passengers: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Danh sách hành khách"
    )


class ExportRequest(BaseModel):
    """Request export dữ liệu"""
    export_type: str = Field(
        ...,
        description="Loại export: users, registrations, flights, vehicles, hotels, gala"
    )
    event_id: Optional[str] = None
    format: str = Field(default="excel", description="excel hoặc csv")
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Bộ lọc (team_id, work_location, etc.)"
    )
