"""
Flight & Vehicle Allocation Endpoints

Endpoints để BTC (ADMIN) quản lý phân bổ tự động và điều chỉnh thủ công:
- Auto Flight Allocation
- Manual Flight Adjustment
- View Allocation Results
- Clear Allocations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.deps import get_current_user, require_admin_role
from app.db.session import get_db
from app.db.models.register import Registration
from app.db.models.resource import Flight, Vehicle
from app.db.models.user import User, Team
from app.db.models.event import Event
from app.schemas.allocation import (
    FlightAllocationResult,
    ManualFlightAdjustment
)
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    AllocationInProgressException
)
from app.services import alloc_flight_svc, audit_svc
from app.services import alloc_vehicle_svc
from app.schemas.allocation import VehicleAllocationResult, ManualVehicleAdjustment

router = APIRouter()


# ============================================
# AUTO FLIGHT ALLOCATION
# ============================================

@router.post("/flights/auto", response_model=FlightAllocationResult)
async def run_auto_flight_allocation(
        event_id: Optional[str] = None,
        direction: str = "OUTBOUND",
        clear_existing: bool = False,
        request: Request = None,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Chạy thuật toán phân bổ chuyến bay tự động.

    Params:
        event_id: UUID của sự kiện (nếu None, lấy active event)
        clear_existing: Nếu True, xóa phân bổ cũ trước khi chạy

    Returns:
        FlightAllocationResult với thống kê và danh sách unallocated

    Thuật toán ưu tiên:
    1. Team đi cùng nhau > Nguyện vọng cá nhân
    2. Team không vừa 1 chuyến → Đẩy cả Team sang chuyến khác (không tách)
    3. Người không có Team → Xếp theo nguyện vọng cá nhân
    """
    if not event_id:
        event_id = current_user.get("active_event_id")

    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    # Kiểm tra event status
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundException(detail="Sự kiện không tồn tại")

    if event.status == "ALLOCATION_IN_PROGRESS" and not clear_existing:
        raise AllocationInProgressException()

    # Clear existing allocations nếu được yêu cầu
    if clear_existing:
        # Cho phép admin khôi phục một allocation bị kẹt sau crash/restart.
        # Việc này chỉ chạy khi admin chủ động yêu cầu clear_existing.
        if event.status == "ALLOCATION_IN_PROGRESS":
            event.status = "REGISTRATION_CLOSED"
            db.commit()
        cleared_count = alloc_flight_svc.clear_flight_allocations(db, event_id, direction)
        print(f"🗑️  Đã xóa {cleared_count} phân bổ cũ")

        # Ghi audit log
        audit_svc.log_action(
            db=db,
            user_id=current_user['sub'],
            emp_code=current_user['emp_code'],
            action="DELETE",
            entity_type="FLIGHT_ALLOCATION",
            entity_id=event_id,
            old_data={'cleared_count': cleared_count},
            reason="Clear allocations trước khi chạy auto allocation",
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("User-Agent") if request else None
        )

    # Chạy thuật toán
    try:
        # Cập nhật status
        event.status = "ALLOCATION_IN_PROGRESS"
        db.commit()

        result = alloc_flight_svc.run_auto_flight_allocation(db, event_id, direction)

        # Cập nhật status hoàn thành
        if result.success:
            event.status = "ALLOCATION_COMPLETED"
        else:
            event.status = "REGISTRATION_CLOSED"  # Cần xử lý thủ công

        db.commit()

        # Ghi audit log
        audit_svc.log_action(
            db=db,
            user_id=current_user['sub'],
            emp_code=current_user['emp_code'],
            action="ALLOCATE",
            entity_type="FLIGHT_ALLOCATION",
            entity_id=event_id,
            new_data={
                'total_users': result.total_users,
                'allocated_users': result.allocated_users,
                'unallocated_users': result.unallocated_users,
                'success': result.success
            },
            reason="Auto flight allocation",
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("User-Agent") if request else None
        )

        return result

    except Exception as e:
        # Rollback nếu có lỗi
        event.status = "REGISTRATION_CLOSED"
        db.commit()

        print(f"❌ Auto allocation failed: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi chạy phân bổ tự động: {str(e)}"
        )


@router.delete("/flights/clear")
async def clear_flight_allocations(
        event_id: Optional[str] = None,
        direction: str = "OUTBOUND",
        request: Request = None,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Xóa toàn bộ phân bổ chuyến bay (reset về null).

    Sử dụng trước khi chạy lại Auto Allocation.
    """
    if not event_id:
        event_id = current_user.get("active_event_id")

    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    cleared_count = alloc_flight_svc.clear_flight_allocations(db, event_id, direction)

    # Ghi audit log
    audit_svc.log_action(
        db=db,
        user_id=current_user['sub'],
        emp_code=current_user['emp_code'],
        action="DELETE",
        entity_type="FLIGHT_ALLOCATION",
        entity_id=event_id,
        old_data={'cleared_count': cleared_count},
        reason="Clear all flight allocations",
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("User-Agent") if request else None
    )

    return {
        "success": True,
        "cleared_count": cleared_count,
        "message": f"Đã xóa {cleared_count} phân bổ chuyến bay"
    }


# ============================================
# MANUAL FLIGHT ADJUSTMENT
# ============================================

@router.put("/flights/manual", response_model=dict)
async def manual_flight_adjustment(
        adjustment: ManualFlightAdjustment,
        request: Request,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Điều chỉnh phân bổ chuyến bay thủ công.

    BTC có thể:
    - Di chuyển một hoặc nhiều người sang chuyến bay khác
    - Ghi lại lý do điều chỉnh (audit log)

    Validation:
    - Target flight phải còn đủ slot
    - User_ids phải tồn tại và đã có registration
    """
    # Validate target flight tồn tại
    target_flight = db.query(Flight).filter(
        Flight.id == adjustment.target_flight_id
    ).first()

    if not target_flight:
        raise NotFoundException(detail="Chuyến bay đích không tồn tại")

    # Manual allocation must be scoped to the same Event as the target flight.
    for user_id in adjustment.user_ids:
        registration = db.query(Registration).filter(
            Registration.user_id == user_id,
            Registration.event_id == target_flight.event_id,
        ).first()
        if not registration:
            raise BadRequestException(detail="User không thuộc Event của chuyến bay đích")

    # Validate user_ids và đếm số người cần di chuyển
    users_to_move = []
    for user_id in adjustment.user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException(detail=f"Không tìm thấy user {user_id}")

        reg = db.query(Registration).filter(
            Registration.user_id == user_id,
            Registration.event_id == target_flight.event_id,
        ).first()

        if not reg:
            raise NotFoundException(detail=f"User {user.full_name} chưa đăng ký")

        users_to_move.append({
            'user': user,
            'registration': reg
        })

    # Kiểm tra slot còn trống
    from app.services.alloc_flight_svc import _get_available_slots
    assignment_field = "assigned_outbound_flight_id" if target_flight.direction == "OUTBOUND" else "assigned_return_flight_id"
    available = _get_available_slots(db, target_flight.id, target_flight.total_slots, assignment_field)

    if available < len(users_to_move):
        raise BadRequestException(
            detail=f"Chuyến bay {target_flight.flight_code} chỉ còn {available} slot, "
                   f"không đủ cho {len(users_to_move)} người"
        )

    # Lưu old data trước khi thay đổi (để audit log)
    old_allocations = {}
    for item in users_to_move:
        old_flight_id = item['registration'].assigned_flight_id
        old_flight_code = None

        if old_flight_id:
            old_flight = db.query(Flight).filter(Flight.id == old_flight_id).first()
            if old_flight:
                old_flight_code = old_flight.flight_code

        old_allocations[item['user'].id] = {
            'user_name': item['user'].full_name,
            'emp_code': item['user'].emp_code,
            'old_flight_id': old_flight_id,
            'old_flight_code': old_flight_code
        }

    # Thực hiện di chuyển
    moved_names = []
    for item in users_to_move:
        item['registration'].assigned_flight_id = adjustment.target_flight_id
        moved_names.append(item['user'].full_name)

    db.commit()

    # ✅ GHI AUDIT LOG
    audit_svc.log_action(
        db=db,
        user_id=current_user['sub'],
        emp_code=current_user['emp_code'],
        action="MANUAL_ADJUST",
        entity_type="FLIGHT_ALLOCATION",
        entity_id=adjustment.target_flight_id,
        old_data=old_allocations,
        new_data={
            'target_flight_id': adjustment.target_flight_id,
            'target_flight_code': target_flight.flight_code,
            'moved_users': moved_names,
            'moved_count': len(users_to_move)
        },
        reason=adjustment.reason,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )

    print(f"[AUDIT] Admin {current_user['emp_code']} di chuyển {len(users_to_move)} người "
          f"sang chuyến bay {target_flight.flight_code}. Lý do: {adjustment.reason or 'Không có'}")

    return {
        "success": True,
        "moved_count": len(users_to_move),
        "target_flight_code": target_flight.flight_code,
        "moved_users": moved_names,
        "message": f"Đã di chuyển {len(users_to_move)} người sang chuyến bay {target_flight.flight_code}"
    }


# ============================================
# VIEW ALLOCATION RESULTS
# ============================================

@router.get("/flights/results")
async def view_allocation_results(
        event_id: Optional[str] = None,
        group_by: str = "flight",  # "flight" hoặc "team"
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Xem kết quả phân bổ chuyến bay.

    Params:
        group_by: "flight" (nhóm theo chuyến bay) hoặc "team" (nhóm theo team)

    Returns:
        Danh sách kết quả phân bổ với thông tin đầy đủ
    """
    if not event_id:
        event_id = current_user.get("active_event_id")

    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    if group_by == "flight":
        return _view_by_flight(db, event_id)
    elif group_by == "team":
        return _view_by_team(db, event_id)
    else:
        raise BadRequestException(detail="group_by chỉ chấp nhận 'flight' hoặc 'team'")


def _view_by_flight(db: Session, event_id: str):
    """Xem kết quả phân bổ nhóm theo chuyến bay"""
    flights = db.query(Flight).filter(Flight.event_id == event_id).all()

    result = []
    for flight in flights:
        registrations = db.query(Registration).filter(
            Registration.event_id == event_id,
            Registration.assigned_flight_id == flight.id
        ).all()

        passengers = []
        for reg in registrations:
            user = db.query(User).filter(User.id == reg.user_id).first()
            if user:
                passengers.append({
                    'emp_code': user.emp_code,
                    'full_name': user.full_name,
                    'team_name': user.team.name if user.team else None,
                    'desired_shift': reg.desired_shift
                })

        result.append({
            'flight_id': flight.id,
            'flight_code': flight.flight_code,
            'direction': flight.direction,
            'departure_time': flight.departure_time.isoformat() if flight.departure_time else None,
            'origin': flight.origin,
            'destination': flight.destination,
            'total_slots': flight.total_slots,
            'assigned_count': len(passengers),
            'available_slots': flight.total_slots - len(passengers),
            'passengers': passengers
        })

    # Thêm danh sách chưa phân bổ
    unallocated_regs = db.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.is_participating == True,
        Registration.assigned_flight_id == None
    ).all()

    unallocated = []
    for reg in unallocated_regs:
        user = db.query(User).filter(User.id == reg.user_id).first()
        if user:
            unallocated.append({
                'user_id': user.id,
                'emp_code': user.emp_code,
                'full_name': user.full_name,
                'team_name': user.team.name if user.team else None,
                'desired_shift': reg.desired_shift
            })

    return {
        'group_by': 'flight',
        'event_id': event_id,
        'flights': result,
        'unallocated': unallocated,
        'unallocated_count': len(unallocated)
    }


def _view_by_team(db: Session, event_id: str):
    """Xem kết quả phân bổ nhóm theo Team"""
    teams = db.query(Team).filter(Team.event_id == event_id).all()

    result = []
    for team in teams:
        team_registrations = db.query(Registration).filter(
            Registration.event_id == event_id,
            Registration.team_id == team.id,
            Registration.is_participating.is_(True),
        ).all()
        member_ids = [registration.user_id for registration in team_registrations]

        team_data = {
            'team_id': team.id,
            'team_name': team.name,
            "member_count": len(member_ids),
            'members': []
        }

        for registration in team_registrations:
            user = registration.user
            reg = registration

            if reg and reg.is_participating:
                flight_code = None
                if reg.assigned_flight_id:
                    flight = db.query(Flight).filter(
                        Flight.id == reg.assigned_flight_id
                    ).first()
                    if flight:
                        flight_code = flight.flight_code

                team_data['members'].append({
                    'user_id': user.id,
                    'emp_code': user.emp_code,
                    'full_name': user.full_name,
                    'desired_shift': reg.desired_shift,
                    'assigned_flight': flight_code
                })

        result.append(team_data)

    return {
        'group_by': 'team',
        'event_id': event_id,
        'teams': result
    }


# ============================================
# STATISTICS
# ============================================

@router.get("/flights/stats")
async def get_allocation_statistics(
        event_id: Optional[str] = None,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Lấy thống kê phân bổ chuyến bay.

    Returns:
        - Tổng số người tham gia
        - Số người đã phân bổ
        - Số người chưa phân bổ
        - Thống kê theo flight
        - Thống kê theo team
    """
    if not event_id:
        event_id = current_user.get("active_event_id")

    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    # Tổng số người tham gia
    total_participants = db.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.is_participating == True
    ).count()

    # Số người đã phân bổ
    allocated_count = db.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.is_participating == True,
        Registration.assigned_flight_id != None
    ).count()

    # Số người chưa phân bổ
    unallocated_count = total_participants - allocated_count

    # Thống kê theo flight
    flights = db.query(Flight).filter(Flight.event_id == event_id).all()
    flight_stats = []

    for flight in flights:
        assigned = db.query(Registration).filter(
            Registration.event_id == event_id,
            Registration.assigned_flight_id == flight.id
        ).count()

        flight_stats.append({
            'flight_code': flight.flight_code,
            'direction': flight.direction,
            'total_slots': flight.total_slots,
            'assigned_count': assigned,
            'available_slots': flight.total_slots - assigned,
            'utilization_rate': round((assigned / flight.total_slots * 100), 2) if flight.total_slots > 0 else 0
        })

    # Thống kê theo team
    teams = db.query(Team).filter(Team.event_id == event_id).all()
    team_stats = []

    for team in teams:
        team_registrations = db.query(Registration).filter(
            Registration.event_id == event_id,
            Registration.team_id == team.id,
            Registration.is_participating.is_(True),
        ).all()
        member_ids = [registration.user_id for registration in team_registrations]

        allocated_members = db.query(Registration).filter(
            Registration.event_id == event_id,
            Registration.user_id.in_(member_ids),
            Registration.is_participating == True,
            Registration.assigned_flight_id != None
        ).count()

        total_members = db.query(Registration).filter(
            Registration.event_id == event_id,
            Registration.user_id.in_(member_ids),
            Registration.is_participating == True
        ).count()

        team_stats.append({
            'team_name': team.name,
            'total_members': total_members,
            'allocated_members': allocated_members,
            'unallocated_members': total_members - allocated_members,
            'allocation_rate': round((allocated_members / total_members * 100), 2) if total_members > 0 else 0
        })

    return {
        'event_id': event_id,
        'summary': {
            'total_participants': total_participants,
            'allocated_count': allocated_count,
            'unallocated_count': unallocated_count,
            'allocation_rate': round((allocated_count / total_participants * 100), 2) if total_participants > 0 else 0
        },
        'flights': flight_stats,
        'teams': team_stats
    }


# ============================================
# AUTO VEHICLE ALLOCATION
# ============================================

@router.post("/vehicles/auto", response_model=VehicleAllocationResult)
async def run_auto_vehicle_allocation(
        route_type: str,
        event_id: Optional[str] = None,
        clear_existing: bool = False,
        request: Request = None,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Chạy phân xe tự động cho 1 chặng.

    Params:
        route_type: ROUTE_1, ROUTE_2, ROUTE_3, ROUTE_4
        event_id: UUID của sự kiện
        clear_existing: Nếu True, xóa phân bổ cũ của chặng này

    Returns:
        VehicleAllocationResult với thống kê

    Thuật toán ưu tiên:
    1. Người cùng chuyến bay
    2. Người cùng Team
    3. Tối ưu công suất xe
    4. Không vượt sức chứa
    """
    if not event_id:
        event_id = current_user.get("active_event_id")

    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    if clear_existing and event_id:
        # Clear is intentionally handled by the service below; this branch
        # documents that retrying an interrupted allocation is explicit.
        pass

    # Clear existing nếu cần
    if clear_existing:
        cleared = alloc_vehicle_svc.clear_vehicle_allocations(db, event_id, route_type)
        print(f"🗑️  Đã xóa {cleared} phân bổ xe cũ cho chặng {route_type}")

        audit_svc.log_action(
            db=db,
            user_id=current_user['sub'],
            emp_code=current_user['emp_code'],
            action="DELETE",
            entity_type="VEHICLE_ALLOCATION",
            entity_id=event_id,
            old_data={'cleared_count': cleared, 'route_type': route_type},
            reason=f"Clear xe chặng {route_type}",
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("User-Agent") if request else None
        )

    # Chạy phân bổ
    try:
        result = alloc_vehicle_svc.run_auto_vehicle_allocation(db, event_id, route_type)

        # Audit log
        audit_svc.log_action(
            db=db,
            user_id=current_user['sub'],
            emp_code=current_user['emp_code'],
            action="ALLOCATE",
            entity_type="VEHICLE_ALLOCATION",
            entity_id=event_id,
            new_data={
                'route_type': route_type,
                'total_users': result.total_users,
                'allocated_users': result.allocated_users,
                'unallocated_users': result.unallocated_users
            },
            reason=f"Auto vehicle allocation - {route_type}",
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("User-Agent") if request else None
        )

        return result

    except Exception as e:
        print(f"❌ Auto vehicle allocation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi chạy phân xe tự động: {str(e)}"
        )


@router.delete("/vehicles/clear")
async def clear_vehicle_allocations_endpoint(
        route_type: Optional[str] = None,
        event_id: Optional[str] = None,
        request: Request = None,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Xóa phân bổ xe.

    Params:
        route_type: Nếu có, chỉ xóa chặng đó. Nếu None, xóa tất cả.
        event_id: UUID của sự kiện
    """
    if not event_id:
        event_id = current_user.get("active_event_id")

    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    cleared_count = alloc_vehicle_svc.clear_vehicle_allocations(db, event_id, route_type)

    # Audit log
    audit_svc.log_action(
        db=db,
        user_id=current_user['sub'],
        emp_code=current_user['emp_code'],
        action="DELETE",
        entity_type="VEHICLE_ALLOCATION",
        entity_id=event_id,
        old_data={'cleared_count': cleared_count, 'route_type': route_type or 'ALL'},
        reason=f"Clear vehicle allocations - {route_type or 'ALL'}",
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("User-Agent") if request else None
    )

    return {
        "success": True,
        "cleared_count": cleared_count,
        "message": f"Đã xóa {cleared_count} phân bổ xe" + (f" (chặng {route_type})" if route_type else "")
    }


@router.put("/vehicles/manual", response_model=dict)
async def manual_vehicle_adjustment(
        adjustment: ManualVehicleAdjustment,
        request: Request,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Điều chỉnh phân xe thủ công.

    BTC có thể di chuyển người sang xe khác.
    """
    # Validate target vehicle
    target_vehicle = db.query(Vehicle).filter(
        Vehicle.id == adjustment.target_vehicle_id
    ).first()

    if not target_vehicle:
        raise NotFoundException(detail="Xe đích không tồn tại")

    for user_id in adjustment.user_ids:
        if not db.query(Registration).filter(
            Registration.user_id == user_id,
            Registration.event_id == target_vehicle.event_id,
        ).first():
            raise BadRequestException(detail="User không thuộc Event của xe đích")

    if target_vehicle.route_type != adjustment.route_type:
        raise BadRequestException(
            detail=f"Xe {target_vehicle.vehicle_name} không phải là xe chặng {adjustment.route_type}"
        )

    # Map route_type sang field
    route_field_map = {
        "ROUTE_1": "assigned_vehicle_1_id",
        "ROUTE_2": "assigned_vehicle_2_id",
        "ROUTE_3": "assigned_vehicle_3_id",
        "ROUTE_4": "assigned_vehicle_4_id",
    }

    assign_col = route_field_map.get(adjustment.route_type)
    if not assign_col:
        raise BadRequestException(detail="Route type không hợp lệ")

    # Validate users
    users_to_move = []
    for user_id in adjustment.user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException(detail=f"Không tìm thấy user {user_id}")

        reg = db.query(Registration).filter(
            Registration.user_id == user_id,
            Registration.event_id == target_vehicle.event_id,
        ).first()

        if not reg:
            raise NotFoundException(detail=f"User {user.full_name} chưa đăng ký")

        users_to_move.append({
            'user': user,
            'registration': reg
        })

    # Kiểm tra capacity
    assigned_count = db.query(Registration).filter(
        getattr(Registration, assign_col) == target_vehicle.id
    ).count()

    available = target_vehicle.capacity - assigned_count

    if available < len(users_to_move):
        raise BadRequestException(
            detail=f"Xe {target_vehicle.vehicle_name} chỉ còn {available} chỗ, "
                   f"không đủ cho {len(users_to_move)} người"
        )

    # Lưu old data
    old_allocations = {}
    for item in users_to_move:
        old_vehicle_id = getattr(item['registration'], assign_col)
        old_vehicle_name = None

        if old_vehicle_id:
            old_vehicle = db.query(Vehicle).filter(Vehicle.id == old_vehicle_id).first()
            if old_vehicle:
                old_vehicle_name = old_vehicle.vehicle_name

        old_allocations[item['user'].id] = {
            'user_name': item['user'].full_name,
            'emp_code': item['user'].emp_code,
            'old_vehicle_id': old_vehicle_id,
            'old_vehicle_name': old_vehicle_name
        }

    # Di chuyển
    moved_names = []
    for item in users_to_move:
        setattr(item['registration'], assign_col, target_vehicle.id)
        moved_names.append(item['user'].full_name)

    db.commit()

    # Audit log
    audit_svc.log_action(
        db=db,
        user_id=current_user['sub'],
        emp_code=current_user['emp_code'],
        action="MANUAL_ADJUST",
        entity_type="VEHICLE_ALLOCATION",
        entity_id=target_vehicle.id,
        old_data=old_allocations,
        new_data={
            'target_vehicle_id': target_vehicle.id,
            'target_vehicle_name': target_vehicle.vehicle_name,
            'route_type': adjustment.route_type,
            'moved_users': moved_names,
            'moved_count': len(users_to_move)
        },
        reason=adjustment.reason,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )

    return {
        "success": True,
        "moved_count": len(users_to_move),
        "target_vehicle_name": target_vehicle.vehicle_name,
        "route_type": adjustment.route_type,
        "moved_users": moved_names,
        "message": f"Đã di chuyển {len(users_to_move)} người sang xe {target_vehicle.vehicle_name} ({adjustment.route_type})"
    }


# ============================================
# VIEW VEHICLE ALLOCATION RESULTS
# ============================================

@router.get("/vehicles/results")
async def view_vehicle_allocation_results(
        route_type: str,
        event_id: Optional[str] = None,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Xem kết quả phân xe theo chặng.

    Params:
        route_type: ROUTE_1, ROUTE_2, ROUTE_3, ROUTE_4
    """
    if not event_id:
        event_id = current_user.get("active_event_id")

    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    # Lấy danh sách xe của chặng này
    vehicles = db.query(Vehicle).filter(
        Vehicle.event_id == event_id,
        Vehicle.route_type == route_type
    ).all()

    route_field_map = {
        "ROUTE_1": "assigned_vehicle_1_id",
        "ROUTE_2": "assigned_vehicle_2_id",
        "ROUTE_3": "assigned_vehicle_3_id",
        "ROUTE_4": "assigned_vehicle_4_id",
    }

    assign_col = route_field_map.get(route_type)
    if not assign_col:
        raise BadRequestException(detail="Route type không hợp lệ")

    result = []
    for vehicle in vehicles:
        registrations = db.query(Registration).filter(
            Registration.event_id == event_id,
            getattr(Registration, assign_col) == vehicle.id
        ).all()

        passengers = []
        for reg in registrations:
            user = db.query(User).filter(User.id == reg.user_id).first()
            if user:
                passengers.append({
                    'emp_code': user.emp_code,
                    'full_name': user.full_name,
                    'team_name': user.team.name if user.team else None
                })

        # Thông tin captain
        captain_name = None
        captain_phone = None
        if vehicle.captain_id:
            captain = db.query(User).filter(User.id == vehicle.captain_id).first()
            if captain:
                captain_name = captain.full_name
                captain_phone = captain.phone

        result.append({
            'vehicle_id': vehicle.id,
            'vehicle_name': vehicle.vehicle_name,
            'route_type': vehicle.route_type,
            'departure_time': vehicle.departure_time.isoformat() if vehicle.departure_time else None,
            'pickup_location': vehicle.pickup_location,
            'dropoff_location': vehicle.dropoff_location,
            'capacity': vehicle.capacity,
            'assigned_count': len(passengers),
            'available_capacity': vehicle.capacity - len(passengers),
            'captain_name': captain_name,
            'captain_phone': captain_phone,
            'notes': vehicle.notes,
            'passengers': passengers
        })

    # Danh sách người chưa phân bổ
    from app.db.models.register import Registration as Reg

    route_need_map = {
        "ROUTE_1": "need_vehicle_route_1",
        "ROUTE_2": "need_vehicle_route_2",
        "ROUTE_3": "need_vehicle_route_3",
        "ROUTE_4": "need_vehicle_route_4",
    }

    need_col = route_need_map.get(route_type)

    unallocated_regs = db.query(Reg).filter(
        Reg.event_id == event_id,
        getattr(Reg, need_col) == True,
        getattr(Reg, assign_col) == None,
        Reg.is_participating == True
    ).all()

    unallocated = []
    for reg in unallocated_regs:
        user = db.query(User).filter(User.id == reg.user_id).first()
        if user:
            unallocated.append({
                'user_id': user.id,
                'emp_code': user.emp_code,
                'full_name': user.full_name,
                'team_name': user.team.name if user.team else None
            })

    return {
        'route_type': route_type,
        'event_id': event_id,
        'vehicles': result,
        'unallocated': unallocated,
        'unallocated_count': len(unallocated)
    }
