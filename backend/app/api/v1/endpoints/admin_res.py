"""
Admin Resource Management Endpoints

BTC quản lý các nguồn lực:
- Chuyến bay (Flights)
- Xe đưa đón (Vehicles)
- Import từ Excel
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import pandas as pd
from io import BytesIO
import io

from app.core.deps import get_current_user, require_admin_role
from app.db.session import get_db
from app.db.models.resource import Flight, Vehicle
from app.db.models.event import Event
from app.db.models.user import User
from app.schemas.resource import (
    FlightCreate,
    FlightUpdate,
    FlightResponse,
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse
)
from app.core.exceptions import NotFoundException, BadRequestException, ConflictException
from app.services import audit_svc

router = APIRouter()


# ============================================
# FLIGHT MANAGEMENT (Quản lý chuyến bay)
# ============================================

@router.get("/flights", response_model=List[FlightResponse])
async def list_flights(
        event_id: Optional[str] = None,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Lấy danh sách tất cả chuyến bay.

    Nếu event_id được cung cấp, chỉ lấy chuyến bay của event đó.
    Ngược lại, lấy chuyến bay của active event.
    """
    if not event_id:
        event_id = current_user.get("active_event_id")

    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    flights = db.query(Flight).filter(Flight.event_id == event_id).all()

    # Map sang response với thống kê assigned_count
    return [_map_flight_to_response(db, flight) for flight in flights]


@router.get("/flights/{flight_id}", response_model=FlightResponse)
async def get_flight_detail(
        flight_id: str,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """[ADMIN ONLY] Lấy chi tiết một chuyến bay"""
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise NotFoundException(detail="Không tìm thấy chuyến bay")

    return _map_flight_to_response(db, flight)


@router.post("/flights", response_model=FlightResponse, status_code=status.HTTP_201_CREATED)
async def create_flight(
        data: FlightCreate,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Tạo chuyến bay mới.

    Yêu cầu:
    - event_id phải tồn tại
    - flight_code phải unique trong cùng event
    - departure_time < arrival_time
    - total_slots > 0
    """
    # Validate event tồn tại
    event = db.query(Event).filter(Event.id == data.event_id).first()
    if not event:
        raise NotFoundException(detail="Sự kiện không tồn tại")

    # Validate departure_time < arrival_time
    if data.departure_time >= data.arrival_time:
        raise BadRequestException(
            detail="Thời gian khởi hành phải trước thời gian đến"
        )

    # Check duplicate flight_code trong cùng event
    existing = db.query(Flight).filter(
        Flight.event_id == data.event_id,
        Flight.flight_code == data.flight_code
    ).first()

    if existing:
        raise ConflictException(
            detail=f"Mã chuyến bay '{data.flight_code}' đã tồn tại trong sự kiện này"
        )

    # Tạo flight mới
    new_flight = Flight(
        event_id=data.event_id,
        flight_code=data.flight_code,
        direction=data.direction,
        total_slots=data.total_slots,
        departure_time=data.departure_time,
        arrival_time=data.arrival_time,
        origin=data.origin,
        destination=data.destination
    )

    db.add(new_flight)
    db.commit()
    db.refresh(new_flight)

    # Audit log
    audit_svc.log_action(
        db=db,
        user_id=current_user['sub'],
        emp_code=current_user['emp_code'],
        action="CREATE",
        entity_type="FLIGHT",
        entity_id=new_flight.id,
        new_data={
            'flight_code': new_flight.flight_code,
            'direction': new_flight.direction,
            'total_slots': new_flight.total_slots
        },
        reason="Tạo chuyến bay mới"
    )

    return _map_flight_to_response(db, new_flight)


@router.put("/flights/{flight_id}", response_model=FlightResponse)
async def update_flight(
        flight_id: str,
        data: FlightUpdate,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Cập nhật thông tin chuyến bay.

    Không cho phép giảm total_slots xuống dưới số lượng đã phân bổ.
    """
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise NotFoundException(detail="Không tìm thấy chuyến bay")

    # Đếm số người đã được phân bổ
    from app.db.models.register import Registration
    assigned_count = db.query(Registration).filter(
        Registration.assigned_flight_id == flight_id
    ).count()

    # Validate nếu cập nhật total_slots
    if data.total_slots is not None:
        if data.total_slots < assigned_count:
            raise BadRequestException(
                detail=f"Không thể giảm số slot xuống {data.total_slots}. "
                       f"Đã có {assigned_count} người được phân bổ vào chuyến bay này."
            )

    # Validate departure_time < arrival_time nếu cả 2 đều được update
    new_departure = data.departure_time or flight.departure_time
    new_arrival = data.arrival_time or flight.arrival_time

    if new_departure >= new_arrival:
        raise BadRequestException(
            detail="Thời gian khởi hành phải trước thời gian đến"
        )

    # Lưu old data để audit
    old_data = {
        'flight_code': flight.flight_code,
        'direction': flight.direction,
        'total_slots': flight.total_slots,
        'departure_time': flight.departure_time.isoformat() if flight.departure_time else None
    }

    # Update các trường
    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(flight, field, value)

    db.commit()
    db.refresh(flight)

    # Audit log
    audit_svc.log_action(
        db=db,
        user_id=current_user['sub'],
        emp_code=current_user['emp_code'],
        action="UPDATE",
        entity_type="FLIGHT",
        entity_id=flight.id,
        old_data=old_data,
        new_data={
            'flight_code': flight.flight_code,
            'direction': flight.direction,
            'total_slots': flight.total_slots
        },
        reason="Cập nhật thông tin chuyến bay"
    )

    return _map_flight_to_response(db, flight)


@router.delete("/flights/{flight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flight(
        flight_id: str,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Xóa chuyến bay.

    Không cho phép xóa nếu đã có người được phân bổ vào chuyến bay này.
    """
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise NotFoundException(detail="Không tìm thấy chuyến bay")

    # Check xem có ai đã được phân bổ chưa
    from app.db.models.register import Registration
    assigned_count = db.query(Registration).filter(
        Registration.assigned_flight_id == flight_id
    ).count()

    if assigned_count > 0:
        raise BadRequestException(
            detail=f"Không thể xóa chuyến bay này. Đã có {assigned_count} người được phân bổ. "
                   "Vui lòng hủy phân bổ trước khi xóa."
        )

    # Audit log
    audit_svc.log_action(
        db=db,
        user_id=current_user['sub'],
        emp_code=current_user['emp_code'],
        action="DELETE",
        entity_type="FLIGHT",
        entity_id=flight_id,
        old_data={
            'flight_code': flight.flight_code,
            'total_slots': flight.total_slots
        },
        reason="Xóa chuyến bay"
    )

    db.delete(flight)
    db.commit()

    return None


def _map_flight_to_response(db: Session, flight: Flight) -> FlightResponse:
    """Helper function map Flight model sang FlightResponse schema"""
    from app.db.models.register import Registration

    # Đếm số người đã được phân bổ
    assignment_field = Registration.assigned_outbound_flight_id if flight.direction == "OUTBOUND" else Registration.assigned_return_flight_id
    assigned_count = db.query(Registration).filter(
        assignment_field == flight.id,
        Registration.event_id == flight.event_id,
        Registration.is_participating.is_(True),
    ).count()

    available_slots = flight.total_slots - assigned_count

    return FlightResponse(
        id=flight.id,
        event_id=flight.event_id,
        flight_code=flight.flight_code,
        direction=flight.direction,
        total_slots=flight.total_slots,
        departure_time=flight.departure_time,
        arrival_time=flight.arrival_time,
        origin=flight.origin,
        destination=flight.destination,
        assigned_count=assigned_count,
        available_slots=available_slots
    )


# ============================================
# IMPORT EXCEL CHUYẾN BAY
# ============================================

@router.post("/flights/import", response_model=dict)
async def import_flights_from_excel(
        file: UploadFile = File(...),
        event_id: Optional[str] = None,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Import danh sách chuyến bay từ file Excel.

    Format Excel yêu cầu:
    | flight_code | direction | departure_time      | arrival_time        | origin | destination | total_slots |
    |-------------|-----------|---------------------|---------------------|--------|-------------|-------------|
    | VN123       | OUTBOUND  | 2026-10-15 08:00:00 | 2026-10-15 10:00:00 | HAN    | DAD         | 180         |
    | VN124       | RETURN    | 2026-10-17 18:00:00 | 2026-10-17 20:00:00 | DAD    | HAN         | 180         |

    Returns:
        Summary: số flight được import thành công, số lỗi
    """
    if not event_id:
        event_id = current_user.get("active_event_id")

    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    # Validate event tồn tại
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundException(detail="Sự kiện không tồn tại")

    # Đọc file Excel
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))

        print(f"📊 Excel file loaded: {len(df)} rows")

    except Exception as e:
        raise BadRequestException(
            detail=f"Không thể đọc file Excel: {str(e)}"
        )

    # Validate columns
    required_columns = [
        'flight_code', 'direction', 'departure_time', 'arrival_time',
        'origin', 'destination', 'total_slots'
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise BadRequestException(
            detail=f"File Excel thiếu các cột: {', '.join(missing_columns)}"
        )

    # Import flights
    success_count = 0
    error_count = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            # Parse datetime
            departure_time = pd.to_datetime(row['departure_time'])
            arrival_time = pd.to_datetime(row['arrival_time'])

            # Validate
            if departure_time >= arrival_time:
                errors.append(f"Row {idx + 2}: Thời gian khởi hành phải trước thời gian đến")
                error_count += 1
                continue

            # Check duplicate
            existing = db.query(Flight).filter(
                Flight.event_id == event_id,
                Flight.flight_code == str(row['flight_code'])
            ).first()

            if existing:
                # Update thay vì tạo mới
                existing.direction = str(row['direction'])
                existing.departure_time = departure_time
                existing.arrival_time = arrival_time
                existing.origin = str(row['origin'])
                existing.destination = str(row['destination'])
                existing.total_slots = int(row['total_slots'])
            else:
                # Tạo mới
                new_flight = Flight(
                    event_id=event_id,
                    flight_code=str(row['flight_code']),
                    direction=str(row['direction']),
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    origin=str(row['origin']),
                    destination=str(row['destination']),
                    total_slots=int(row['total_slots'])
                )
                db.add(new_flight)

            success_count += 1

        except Exception as e:
            errors.append(f"Row {idx + 2}: {str(e)}")
            error_count += 1

    # Commit
    db.commit()

    # Log audit
    audit_svc.log_action(
        db=db,
        user_id=current_user['sub'],
        emp_code=current_user['emp_code'],
        action="IMPORT",
        entity_type="FLIGHT",
        entity_id=event_id,
        new_data={
            'total_rows': len(df),
            'success_count': success_count,
            'error_count': error_count
        },
        reason=f"Import {success_count} chuyến bay từ Excel"
    )

    print(f"[AUDIT] Admin {current_user['emp_code']} imported {success_count} flights to event {event_id}")

    return {
        "success": True,
        "total_rows": len(df),
        "success_count": success_count,
        "error_count": error_count,
        "errors": errors if error_count > 0 else [],
        "message": f"Import hoàn tất: {success_count} thành công, {error_count} lỗi"
    }


@router.get("/flights/export-template")
async def export_flights_template(
        current_user: dict = Depends(require_admin_role)
):
    """
    [ADMIN ONLY] Download template Excel để import chuyến bay.

    Returns:
        Excel file với format mẫu
    """
    # Tạo DataFrame mẫu
    template_data = {
        'flight_code': ['VN123', 'VN124', 'VJ456'],
        'direction': ['OUTBOUND', 'RETURN', 'OUTBOUND'],
        'departure_time': ['2026-10-15 08:00:00', '2026-10-17 18:00:00', '2026-10-15 14:00:00'],
        'arrival_time': ['2026-10-15 10:00:00', '2026-10-17 20:00:00', '2026-10-15 16:00:00'],
        'origin': ['HAN', 'DAD', 'HAN'],
        'destination': ['DAD', 'HAN', 'DAD'],
        'total_slots': [180, 180, 150]
    }

    df = pd.DataFrame(template_data)

    # Tạo Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Flights')

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=flight_import_template.xlsx"
        }
    )


# ============================================
# VEHICLE MANAGEMENT (Quản lý xe - TODO)
# ============================================

@router.get("/vehicles")
async def list_vehicles(
        event_id: Optional[str] = None,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Lấy danh sách xe.

    TODO: Implement đầy đủ như Flight management
    """
    if not event_id:
        event_id = current_user.get("active_event_id")

    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    vehicles = db.query(Vehicle).filter(Vehicle.event_id == event_id).all()

    return {
        "vehicles": [
            {
                "id": v.id,
                "vehicle_name": v.vehicle_name,
                "route_type": v.route_type,
                "capacity": v.capacity,
                "pickup_location": v.pickup_location
            }
            for v in vehicles
        ]
    }
