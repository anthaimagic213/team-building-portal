from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class FlightDirection(str, Enum):
    """Direction of flight"""
    OUTBOUND = "OUTBOUND"  # Chuyến đi (HN/HCM → Destination)
    RETURN = "RETURN"  # Chuyến về (Destination → HN/HCM)


class RouteType(str, Enum):
    """
    4 chặng di chuyển trong hành trình Team Building.

    ROUTE_1: Văn phòng HN/HCM → Sân bay Nội Bài/Tân Sơn Nhất
    ROUTE_2: Sân bay Đà Nẵng/Phú Quốc → Khách sạn
    ROUTE_3: Khách sạn → Sân bay Đà Nẵng/Phú Quốc
    ROUTE_4: Sân bay Nội Bài/Tân Sơn Nhất → Văn phòng HN/HCM
    """
    ROUTE_1_OFFICE_TO_AIRPORT = "ROUTE_1"
    ROUTE_2_AIRPORT_TO_HOTEL = "ROUTE_2"
    ROUTE_3_HOTEL_TO_AIRPORT = "ROUTE_3"
    ROUTE_4_AIRPORT_TO_OFFICE = "ROUTE_4"


# ============================================
# FLIGHT SCHEMAS
# ============================================

class FlightBase(BaseModel):
    """Base schema for Flight"""
    flight_code: str = Field(..., description="Mã chuyến bay (VD: VN123, VJ456)")
    direction: FlightDirection = Field(..., description="Chiều bay: OUTBOUND (đi) hoặc RETURN (về)")
    total_slots: int = Field(..., ge=0, description="Tổng số ghế")
    departure_time: datetime = Field(..., description="Thời gian khởi hành (ISO8601)")
    arrival_time: datetime = Field(..., description="Thời gian đến (ISO8601)")
    origin: str = Field(..., description="Sân bay xuất phát (HAN, SGN)")
    destination: str = Field(..., description="Sân bay đích (DAD, PQC)")


class FlightCreate(FlightBase):
    """Schema for creating a new flight"""
    event_id: str = Field(..., description="Event UUID")


class FlightUpdate(BaseModel):
    """Schema for updating flight information"""
    flight_code: Optional[str] = None
    direction: Optional[FlightDirection] = None
    total_slots: Optional[int] = Field(None, ge=0)
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    origin: Optional[str] = None
    destination: Optional[str] = None


class FlightResponse(FlightBase):
    """Flight response with allocation statistics"""
    id: str = Field(..., description="Flight UUID")
    event_id: str = Field(..., description="Event UUID")
    assigned_count: int = Field(default=0, description="Số người đã được phân bổ")
    available_slots: int = Field(default=0, description="Số ghế còn trống")

    class Config:
        from_attributes = True


# ============================================
# VEHICLE SCHEMAS
# ============================================

class VehicleBase(BaseModel):
    """Base schema for Vehicle"""
    vehicle_name: str = Field(..., description="Tên xe (VD: Bus 01, Xe 15 chỗ A)")
    route_type: RouteType = Field(..., description="Loại chặng (ROUTE_1, ROUTE_2, ROUTE_3, ROUTE_4)")
    departure_time: datetime = Field(..., description="Thời gian khởi hành (ISO8601)")
    pickup_location: str = Field(..., description="Địa điểm đón (VD: Văn phòng HN, Sân bay Đà Nẵng)")
    dropoff_location: Optional[str] = Field(None, description="Địa điểm trả (VD: Sân bay, Khách sạn X)")
    capacity: int = Field(..., ge=0, description="Sức chứa (số người)")
    captain_id: Optional[str] = Field(None, description="UUID của Trưởng xe (User)")
    notes: Optional[str] = Field(None, description="Ghi chú (VD: Xe có wifi, nước uống...)")


class VehicleCreate(VehicleBase):
    """Schema for creating a new vehicle"""
    event_id: str = Field(..., description="Event UUID")


class VehicleUpdate(BaseModel):
    """Schema for updating vehicle information"""
    vehicle_name: Optional[str] = None
    route_type: Optional[RouteType] = None
    departure_time: Optional[datetime] = None
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=0)
    captain_id: Optional[str] = None
    notes: Optional[str] = None


class VehicleResponse(VehicleBase):
    """Vehicle response with allocation statistics"""
    id: str = Field(..., description="Vehicle UUID")
    event_id: str = Field(..., description="Event UUID")
    captain_name: Optional[str] = Field(None, description="Tên Trưởng xe")
    captain_phone: Optional[str] = Field(None, description="SĐT Trưởng xe")
    assigned_count: int = Field(default=0, description="Số người đã được phân bổ")
    available_capacity: int = Field(default=0, description="Số chỗ còn trống")

    class Config:
        from_attributes = True


"""
═══════════════════════════════════════════════════════════════════
                    MÔ TẢ CHI TIẾT 4 CHẶNG XE
═══════════════════════════════════════════════════════════════════

ROUTE_1: Văn phòng HN/HCM → Sân bay Nội Bài/Tân Sơn Nhất
────────────────────────────────────────────────────────────────
- Thời gian: Sáng sớm ngày đi (VD: 6:00 AM)
- Pickup: Văn phòng công ty (user có thể chọn điểm đón mong muốn)
- Dropoff: Sân bay Nội Bài (HAN) hoặc Tân Sơn Nhất (SGN)
- Mục đích: Đưa nhân viên từ văn phòng ra sân bay để bay sang địa điểm
- Lưu ý: 
  * Một số nhân viên có thể tự đi (không cần xe)
  * Có thể có nhiều điểm đón khác nhau (văn phòng HN, HCM, chi nhánh...)

ROUTE_2: Sân bay Đà Nẵng/Phú Quốc → Khách sạn
────────────────────────────────────────────────────────────────
- Thời gian: Sau khi máy bay hạ cánh (VD: 10:30 AM)
- Pickup: Sân bay Đà Nẵng (DAD) hoặc Phú Quốc (PQC)
- Dropoff: Khách sạn X
- Mục đích: Đón nhân viên từ sân bay về khách sạn nghỉ ngơi
- Lưu ý:
  * Phải sync với chuyến bay (cùng flight → cùng xe)
  * Xe chờ sẵn ở sân bay khi máy bay hạ cánh

ROUTE_3: Khách sạn → Sân bay Đà Nẵng/Phú Quốc
────────────────────────────────────────────────────────────────
- Thời gian: Trước giờ bay về 2-3 tiếng (VD: 3:00 PM)
- Pickup: Khách sạn X
- Dropoff: Sân bay Đà Nẵng (DAD) hoặc Phú Quốc (PQC)
- Mục đích: Đưa nhân viên từ khách sạn ra sân bay để bay về
- Lưu ý:
  * Phải đảm bảo đến sân bay trước giờ bay ít nhất 2 tiếng
  * Cùng chuyến bay → cùng xe

ROUTE_4: Sân bay Nội Bài/Tân Sơn Nhất → Văn phòng HN/HCM
────────────────────────────────────────────────────────────────
- Thời gian: Sau khi máy bay về đến HN/HCM (VD: 8:00 PM)
- Pickup: Sân bay Nội Bài (HAN) hoặc Tân Sơn Nhất (SGN)
- Dropoff: Văn phòng hoặc điểm trả mong muốn của nhân viên
- Mục đích: Đưa nhân viên từ sân bay về văn phòng/nhà
- Lưu ý:
  * Một số nhân viên có thể có người nhà đón (không cần xe)
  * Có thể có nhiều điểm trả khác nhau

═══════════════════════════════════════════════════════════════════
"""
