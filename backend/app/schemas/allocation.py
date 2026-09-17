from pydantic import BaseModel, Field
from typing import List, Optional


class FlightAllocationResult(BaseModel):
    """Kết quả phân bổ chuyến bay tự động"""
    success: bool = Field(..., description="Phân bổ thành công 100% hay không")
    total_users: int = Field(..., description="Tổng số người cần phân bổ")
    allocated_users: int = Field(..., description="Số người đã phân bổ thành công")
    unallocated_users: int = Field(..., description="Số người chưa phân bổ được")
    unallocated_user_ids: List[str] = Field(default_factory=list, description="Danh sách user_id chưa phân bổ")
    warnings: List[str] = Field(default_factory=list, description="Các cảnh báo")
    message: str = Field(..., description="Thông báo kết quả")


class ManualFlightAdjustment(BaseModel):
    """Request để điều chỉnh phân bổ chuyến bay thủ công"""
    user_ids: List[str] = Field(..., description="Danh sách UUID của users cần di chuyển")
    target_flight_id: str = Field(..., description="UUID của chuyến bay đích")
    reason: Optional[str] = Field(None, description="Lý do điều chỉnh")


class VehicleAllocationResult(BaseModel):
    """Kết quả phân bổ xe tự động"""
    success: bool = Field(..., description="Phân bổ thành công 100% hay không")
    route_type: str = Field(..., description="Chặng xe (ROUTE_1, ROUTE_2, ROUTE_3, ROUTE_4)")
    total_users: int = Field(..., description="Tổng số người cần xe")
    allocated_users: int = Field(..., description="Số người đã xếp xe")
    unallocated_users: int = Field(..., description="Số người chưa xếp được xe")
    unallocated_user_ids: List[str] = Field(default_factory=list, description="Danh sách user_id chưa xếp")
    message: str = Field(..., description="Thông báo kết quả")


class ManualVehicleAdjustment(BaseModel):
    """Request để điều chỉnh phân xe thủ công"""
    user_ids: List[str] = Field(..., description="Danh sách UUID của users cần di chuyển")
    target_vehicle_id: str = Field(..., description="UUID của xe đích")
    route_type: str = Field(..., description="Chặng xe (ROUTE_1, ROUTE_2, ROUTE_3, ROUTE_4)")
    reason: Optional[str] = Field(None, description="Lý do điều chỉnh")



class HotelImportResult(BaseModel):
    """Result of hotel room assignment import from Excel"""
    success: bool
    total_rows: int = Field(..., description="Total rows processed")
    successful_imports: int
    failed_imports: int
    errors: List[str] = Field(default=[], description="Error messages for failed rows")
    message: str
