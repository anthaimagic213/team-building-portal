"""
Auto Flight Allocation Service

Thuật toán CSP (Constraint Satisfaction Problem) phân bổ chuyến bay:

NGUYÊN TẮC ƯU TIÊN:
1. Team đi cùng nhau > Nguyện vọng cá nhân (desired_shift)
2. Nếu Team không vừa 1 chuyến → Đẩy cả Team sang chuyến khác
3. Không tách người trong cùng Team
4. Người không có Team → Xếp theo nguyện vọng cá nhân

THUẬT TOÁN:
1. Lấy danh sách registrations (is_participating = True)
2. Nhóm theo Team
3. Sắp xếp flights theo departure_time
4. Xử lý từng Team:
   - Tìm chuyến bay phù hợp (shift + available_slots >= team_size)
   - Nếu tìm được → Phân bổ cả Team
   - Nếu không tìm được → Đẩy vào unallocated
5. Xử lý người không có Team theo nguyện vọng cá nhân
6. Trả về kết quả + danh sách unallocated cần xử lý thủ công
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Tuple
from datetime import time
from app.db.models.register import Registration
from app.db.models.resource import Flight
from app.db.models.user import User, Team
from app.schemas.allocation import FlightAllocationResult


def run_auto_flight_allocation(db: Session, event_id: str, direction: str = "OUTBOUND") -> FlightAllocationResult:
    """
    Chạy thuật toán phân bổ chuyến bay tự động.

    Args:
        db: Database session
        event_id: UUID của sự kiện

    Returns:
        FlightAllocationResult với thống kê và danh sách unallocated
    """
    # 1. Lấy danh sách registrations (chỉ is_participating = True)
    registrations = db.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.is_participating == True
    ).all()

    if not registrations:
        return FlightAllocationResult(
            success=True,
            total_users=0,
            allocated_users=0,
            unallocated_users=0,
            unallocated_user_ids=[],
            warnings=[],
            message="Không có ai đăng ký tham gia"
        )

    # 2. Lấy danh sách flights và sắp xếp theo departure_time
    direction = direction.upper()
    if direction not in ("OUTBOUND", "RETURN"):
        raise ValueError("direction must be OUTBOUND or RETURN")
    assignment_field = "assigned_outbound_flight_id" if direction == "OUTBOUND" else "assigned_return_flight_id"
    flights = db.query(Flight).filter(
        Flight.event_id == event_id,
        Flight.direction == direction,
    ).order_by(Flight.departure_time).all()

    if not flights:
        return FlightAllocationResult(
            success=False,
            total_users=len(registrations),
            allocated_users=0,
            unallocated_users=len(registrations),
            unallocated_user_ids=[r.user_id for r in registrations],
            warnings=["Không có chuyến bay nào được cấu hình"],
            message="Vui lòng thêm chuyến bay trước khi chạy phân bổ"
        )

    # 3. Nhóm registrations theo Team
    team_groups = _group_by_team(db, registrations)

    # 4. Phân loại flights theo shift (SHIFT_1: trước 17:00, SHIFT_2: sau 17:00)
    shift_flights = _classify_flights_by_shift(flights)

    # 5. Tracking. Keep capacity in memory so assignments made earlier in
    # this transaction are immediately reflected in the next decision.
    allocated_count = 0
    unallocated_user_ids = []
    warnings = []
    remaining_capacity = {
        flight.id: flight.total_slots
        for flight in flights
    }

    # 6. Xử lý từng Team: ưu tiên xếp cả Team, sau đó tách Team nếu cần.
    sorted_teams = sorted(
        team_groups['with_team'].items(),
        key=lambda x: len(x[1]),
        reverse=True
    )

    for team_id, team_regs in sorted_teams:
        team = db.query(Team).filter(Team.id == team_id).first()
        team_name = team.name if team else "Unknown Team"
        team_size = len(team_regs)

        # Lấy shift mong muốn (majority vote trong team)
        preferred_shift = _get_team_preferred_shift(team_regs)

        # Tìm chuyến bay phù hợp cho cả Team
        suitable_flights = shift_flights.get(preferred_shift, [])

        # First use the preferred shift, then the other shift. A Team may be
        # split across flights when no single flight has enough capacity.
        other_shift = "SHIFT_2" if preferred_shift == "SHIFT_1" else "SHIFT_1"
        candidate_flights = suitable_flights + [
            flight for flight in shift_flights.get(other_shift, [])
            if flight not in suitable_flights
        ]
        remaining = list(team_regs)
        for flight in candidate_flights:
            slots = remaining_capacity[flight.id]
            batch = remaining[:slots]
            for reg in batch:
                setattr(reg, assignment_field, flight.id)
            remaining = remaining[len(batch):]
            remaining_capacity[flight.id] -= len(batch)
            allocated_count += len(batch)
            if not remaining:
                break

        if remaining:
            unallocated_user_ids.extend(reg.user_id for reg in remaining)
            warnings.append(
                f"Team '{team_name}' được tách chuyến; còn {len(remaining)} người chưa có chỗ"
            )
        elif len({getattr(reg, assignment_field) for reg in team_regs}) > 1:
            warnings.append(f"Team '{team_name}' được chia ra nhiều chuyến do giới hạn capacity")

    # 7. Xử lý người không có Team (xếp theo nguyện vọng cá nhân)
    no_team_regs = team_groups['no_team']

    for reg in no_team_regs:
        preferred_shift = reg.desired_shift or "SHIFT_1"
        suitable_flights = shift_flights.get(preferred_shift, [])

        other_shift = "SHIFT_2" if preferred_shift == "SHIFT_1" else "SHIFT_1"
        candidate_flights = suitable_flights + [flight for flight in shift_flights.get(other_shift, []) if flight not in suitable_flights]
        allocated = False
        for flight in candidate_flights:
            if remaining_capacity[flight.id] > 0:
                setattr(reg, assignment_field, flight.id)
                remaining_capacity[flight.id] -= 1
                allocated_count += 1
                allocated = True
                break
        if not allocated:
            unallocated_user_ids.append(reg.user_id)

    # 8. Commit changes
    db.commit()

    # 9. Return result
    total_users = len(registrations)
    unallocated_count = len(unallocated_user_ids)

    return FlightAllocationResult(
        success=unallocated_count == 0,
        total_users=total_users,
        allocated_users=allocated_count,
        unallocated_users=unallocated_count,
        unallocated_user_ids=unallocated_user_ids,
        warnings=warnings,
        message=f"Phân bổ thành công {allocated_count}/{total_users} người. "
                f"{unallocated_count} người cần xử lý thủ công." if unallocated_count > 0
        else f"Phân bổ thành công toàn bộ {total_users} người!"
    )


def _group_by_team(db: Session, registrations: List[Registration]) -> Dict[str, List[Registration]]:
    """Nhóm registrations theo Team"""
    result = {
        'with_team': {},  # {team_id: [registrations]}
        'no_team': []  # [registrations without team]
    }

    for reg in registrations:
        user = db.query(User).filter(User.id == reg.user_id).first()

        if user and reg.team_id:
            if reg.team_id not in result['with_team']:
                result['with_team'][reg.team_id] = []
            result['with_team'][reg.team_id].append(reg)
        else:
            result['no_team'].append(reg)

    return result


def _classify_flights_by_shift(flights: List[Flight]) -> Dict[str, List[Flight]]:
    """
    Phân loại flights theo shift.

    SHIFT_1: departure_time < 17:00
    SHIFT_2: departure_time >= 17:00
    """
    result = {
        'SHIFT_1': [],
        'SHIFT_2': []
    }

    cutoff_time = time(17, 0)  # 17:00

    for flight in flights:
        flight_time = flight.departure_time.time()

        if flight_time < cutoff_time:
            result['SHIFT_1'].append(flight)
        else:
            result['SHIFT_2'].append(flight)

    return result


def _get_team_preferred_shift(team_regs: List[Registration]) -> str:
    """
    Lấy shift mong muốn của Team (majority vote).

    Nếu tie → Chọn SHIFT_1
    """
    shift_1_count = sum(1 for r in team_regs if r.desired_shift == "SHIFT_1")
    shift_2_count = sum(1 for r in team_regs if r.desired_shift == "SHIFT_2")

    return "SHIFT_1" if shift_1_count >= shift_2_count else "SHIFT_2"


def _get_available_slots(db: Session, flight_id: str, total_slots: int, assignment_field: str = "assigned_outbound_flight_id") -> int:
    """Tính số slot còn trống của một chuyến bay"""
    assigned_count = db.query(Registration).filter(getattr(Registration, assignment_field) == flight_id).count()

    return total_slots - assigned_count


def clear_flight_allocations(db: Session, event_id: str, direction: str = "OUTBOUND") -> int:
    """
    Xóa toàn bộ phân bổ chuyến bay (reset về null).

    Returns:
        Số lượng registrations đã được reset
    """
    field = Registration.assigned_outbound_flight_id if direction.upper() == "OUTBOUND" else Registration.assigned_return_flight_id
    result = db.query(Registration).filter(Registration.event_id == event_id).update({field: None})

    db.commit()

    return result
