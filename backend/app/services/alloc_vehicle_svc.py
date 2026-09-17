"""
Vehicle Auto Allocation Service

Thuật toán phân xe tự động dựa trên:
1. Người cùng chuyến bay (ưu tiên cao nhất)
2. Người cùng Team
3. Tối ưu công suất xe
4. Không vượt sức chứa
"""

from sqlalchemy.orm import Session
from typing import Dict, List
from app.db.models.register import Registration
from app.db.models.resource import Vehicle, Flight
from app.db.models.user import User, Team
from app.schemas.allocation import VehicleAllocationResult


def run_auto_vehicle_allocation(
        db: Session,
        event_id: str,
        route_type: str
) -> VehicleAllocationResult:
    """
    Chạy phân xe tự động cho 1 chặng cụ thể.

    Args:
        db: Database session
        event_id: UUID của sự kiện
        route_type: ROUTE_1, ROUTE_2, ROUTE_3, ROUTE_4

    Returns:
        VehicleAllocationResult với thống kê
    """

    # 1. Lấy danh sách xe của chặng này
    vehicles = db.query(Vehicle).filter(
        Vehicle.event_id == event_id,
        Vehicle.route_type == route_type
    ).order_by(Vehicle.capacity.desc()).all()

    if not vehicles:
        return VehicleAllocationResult(
            success=False,
            route_type=route_type,
            total_users=0,
            allocated_users=0,
            unallocated_users=0,
            unallocated_user_ids=[],
            message=f"Không có xe nào cho chặng {route_type}"
        )

    # 2. Map route_type sang field trong Registration
    route_field_map = {
        "ROUTE_1": ("need_vehicle_route_1", "assigned_vehicle_1_id"),
        "ROUTE_2": ("need_vehicle_route_2", "assigned_vehicle_2_id"),
        "ROUTE_3": ("need_vehicle_route_3", "assigned_vehicle_3_id"),
        "ROUTE_4": ("need_vehicle_route_4", "assigned_vehicle_4_id"),
    }

    need_col, assign_col = route_field_map.get(route_type, (None, None))
    if not need_col:
        return VehicleAllocationResult(
            success=False,
            route_type=route_type,
            total_users=0,
            allocated_users=0,
            unallocated_users=0,
            unallocated_user_ids=[],
            message=f"Route type {route_type} không hợp lệ"
        )

    # 3. Lấy danh sách người cần xe chặng này (chưa được phân bổ)
    unassigned_regs = db.query(Registration).join(User).filter(
        Registration.event_id == event_id,
        getattr(Registration, need_col) == True,
        getattr(Registration, assign_col).is_(None),
        Registration.is_participating == True
    ).all()

    if not unassigned_regs:
        return VehicleAllocationResult(
            success=True,
            route_type=route_type,
            total_users=0,
            allocated_users=0,
            unallocated_users=0,
            unallocated_user_ids=[],
            message=f"Không có ai cần xe chặng {route_type}"
        )

    # 4. Nhóm theo Flight (nếu có) -> Team
    grouped_data = _group_by_flight_and_team(unassigned_regs)

    # 5. Khởi tạo capacity tracking
    vehicle_capacity = {v.id: v.capacity for v in vehicles}

    # 6. Phân bổ theo thứ tự ưu tiên
    allocated_count = 0
    unallocated_ids = []

    # Ưu tiên 1: Cùng Flight + Cùng Team
    for flight_id, teams in grouped_data.items():
        for team_id, members in teams.items():
            team_size = len(members)
            allocated = False

            # Tìm xe còn đủ chỗ
            for vehicle in vehicles:
                if vehicle_capacity[vehicle.id] >= team_size:
                    # Gán cả nhóm vào xe này
                    for member in members:
                        setattr(member, assign_col, vehicle.id)

                    vehicle_capacity[vehicle.id] -= team_size
                    allocated_count += team_size
                    allocated = True

                    print(
                        f"✅ Đã xếp {team_size} người (Flight: {flight_id or 'N/A'}, Team: {team_id}) vào xe {vehicle.vehicle_name}")
                    break

            # Nếu không tìm được xe đủ chỗ cho cả team
            if not allocated:
                # Thử chia nhỏ team ra nhiều xe
                remaining = members[:]
                while remaining and any(cap > 0 for cap in vehicle_capacity.values()):
                    for vehicle in vehicles:
                        if vehicle_capacity[vehicle.id] > 0:
                            # Lấy tối đa số người vừa xe
                            batch_size = min(len(remaining), vehicle_capacity[vehicle.id])
                            batch = remaining[:batch_size]

                            for member in batch:
                                setattr(member, assign_col, vehicle.id)

                            vehicle_capacity[vehicle.id] -= batch_size
                            allocated_count += batch_size
                            remaining = remaining[batch_size:]

                            print(f"⚠️  Đã tách {batch_size} người từ Team {team_id} vào xe {vehicle.vehicle_name}")

                            if not remaining:
                                break

                # Những người còn lại không xếp được
                if remaining:
                    unallocated_ids.extend([m.user_id for m in remaining])
                    print(f"❌ Không thể xếp {len(remaining)} người (Team {team_id})")

    # Commit
    db.commit()

    total_users = len(unassigned_regs)
    unallocated_users = len(unallocated_ids)
    success = unallocated_users == 0

    return VehicleAllocationResult(
        success=success,
        route_type=route_type,
        total_users=total_users,
        allocated_users=allocated_count,
        unallocated_users=unallocated_users,
        unallocated_user_ids=unallocated_ids,
        message=f"Phân bổ xe chặng {route_type}: {allocated_count}/{total_users} người"
    )


def _group_by_flight_and_team(registrations: List[Registration]) -> Dict:
    """
    Nhóm registrations theo Flight -> Team.

    Returns:
        {
            flight_id: {
                team_id: [reg1, reg2, ...],
                ...
            },
            ...
        }
    """
    grouped = {}

    for reg in registrations:
        # Flight ID (None nếu chưa có)
        f_id = reg.assigned_flight_id or "NO_FLIGHT"

        # Team ID (None nếu không có team)
        t_id = reg.team_id or "NO_TEAM"

        if f_id not in grouped:
            grouped[f_id] = {}

        if t_id not in grouped[f_id]:
            grouped[f_id][t_id] = []

        grouped[f_id][t_id].append(reg)

    return grouped


def clear_vehicle_allocations(
        db: Session,
        event_id: str,
        route_type: str = None
) -> int:
    """
    Xóa phân bổ xe.

    Args:
        db: Database session
        event_id: UUID của sự kiện
        route_type: Nếu có, chỉ xóa chặng đó. Nếu None, xóa tất cả.

    Returns:
        Số lượng registrations đã bị clear
    """
    query = db.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.is_participating == True
    )

    if route_type:
        # Clear chỉ 1 chặng
        route_field_map = {
            "ROUTE_1": "assigned_vehicle_1_id",
            "ROUTE_2": "assigned_vehicle_2_id",
            "ROUTE_3": "assigned_vehicle_3_id",
            "ROUTE_4": "assigned_vehicle_4_id",
        }

        assign_col = route_field_map.get(route_type)
        if not assign_col:
            return 0

        regs = query.filter(getattr(Registration, assign_col).isnot(None)).all()

        for reg in regs:
            setattr(reg, assign_col, None)

        db.commit()
        return len(regs)

    else:
        # Clear tất cả các chặng
        regs = query.all()
        count = 0

        for reg in regs:
            if reg.assigned_vehicle_1_id:
                reg.assigned_vehicle_1_id = None
                count += 1
            if reg.assigned_vehicle_2_id:
                reg.assigned_vehicle_2_id = None
                count += 1
            if reg.assigned_vehicle_3_id:
                reg.assigned_vehicle_3_id = None
                count += 1
            if reg.assigned_vehicle_4_id:
                reg.assigned_vehicle_4_id = None
                count += 1

        db.commit()
        return count
