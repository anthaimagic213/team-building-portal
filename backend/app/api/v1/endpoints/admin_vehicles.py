"""
Admin Vehicle Management Endpoints

BTC quản lý xe đưa đón:
- CRUD xe (Create, Read, Update, Delete)
- Import từ Excel
- Chỉ định Trưởng xe
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
from io import BytesIO
import io

from app.core.deps import require_admin_role
from app.db.session import get_db
from app.db.models.resource import Vehicle
from app.db.models.event import Event
from app.db.models.user import User
from app.schemas.resource import VehicleCreate, VehicleUpdate, VehicleResponse
from app.core.exceptions import NotFoundException, BadRequestException, ConflictException
from app.services import audit_svc

router = APIRouter()


@router.get("", response_model=List[VehicleResponse])
async def list_vehicles(
    event_id: Optional[str] = None,
    route_type: Optional[str] = None,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Lấy danh sách xe.

    Params:
        event_id: UUID của sự kiện (nếu None, lấy active event)
        route_type: Lọc theo chặng (ROUTE_1, ROUTE_2, ROUTE_3, ROUTE_4)
    """
    if not event_id:
        event_id = current_user.get("active_event_id")

    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    query = db.query(Vehicle).filter(Vehicle.event_id == event_id)

    if route_type:
        query = query.filter(Vehicle.route_type == route_type)

    vehicles = query.all()

    return [_map_vehicle_to_response(db, vehicle) for vehicle in vehicles]


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle_detail(
    vehicle_id: str,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """[ADMIN ONLY] Lấy chi tiết 1 xe"""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise NotFoundException(detail="Không tìm thấy xe")

    return _map_vehicle_to_response(db, vehicle)


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    data: VehicleCreate,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Tạo xe mới.

    Yêu cầu:
    - event_id phải tồn tại
    - vehicle_name phải unique trong cùng event + route
    - capacity > 0
    - captain_id phải tồn tại (nếu có)
    """
    # Validate event
    event = db.query(Event).filter(Event.id == data.event_id).first()
    if not event:
        raise NotFoundException(detail="Sự kiện không tồn tại")

    # Validate captain (nếu có)
    if data.captain_id:
        captain = db.query(User).filter(User.id == data.captain_id).first()
        if not captain:
            raise NotFoundException(detail="Không tìm thấy Trưởng xe")

    # Check duplicate vehicle_name
    existing = db.query(Vehicle).filter(
        Vehicle.event_id == data.event_id,
        Vehicle.route_type == data.route_type,
        Vehicle.vehicle_name == data.vehicle_name
    ).first()

    if existing:
        raise ConflictException(
            detail=f"Xe '{data.vehicle_name}' đã tồn tại trong chặng {data.route_type}"
        )

    # Tạo xe mới
    new_vehicle = Vehicle(
        event_id=data.event_id,
        vehicle_name=data.vehicle_name,
        route_type=data.route_type,
        departure_time=data.departure_time,
        pickup_location=data.pickup_location,
        dropoff_location=data.dropoff_location,
        capacity=data.capacity,
        captain_id=data.captain_id,
        notes=data.notes
    )

    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)

    # Audit log
    audit_svc.log_action(
        db=db,
        user_id=current_user['sub'],
        emp_code=current_user['emp_code'],
        action="CREATE",
        entity_type="VEHICLE",
        entity_id=new_vehicle.id,
        new_data={
            'vehicle_name': new_vehicle.vehicle_name,
            'route_type': new_vehicle.route_type,
            'capacity': new_vehicle.capacity
        },
        reason="Tạo xe mới"
    )

    return _map_vehicle_to_response(db, new_vehicle)


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: str,
    data: VehicleUpdate,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Cập nhật thông tin xe.

    Không cho phép giảm capacity xuống dưới số người đã phân bổ.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise NotFoundException(detail="Không tìm thấy xe")

    # Đếm số người đã được phân bổ
    from app.db.models.register import Registration

    route_field_map = {
        "ROUTE_1": "assigned_vehicle_1_id",
        "ROUTE_2": "assigned_vehicle_2_id",
        "ROUTE_3": "assigned_vehicle_3_id",
        "ROUTE_4": "assigned_vehicle_4_id",
    }

    assign_col = route_field_map.get(vehicle.route_type)
    if assign_col:
        assigned_count = db.query(Registration).filter(
            getattr(Registration, assign_col) == vehicle_id
        ).count()

        # Validate capacity
        if data.capacity is not None and data.capacity < assigned_count:
            raise BadRequestException(
                detail=f"Không thể giảm capacity xuống {data.capacity}. "
                       f"Đã có {assigned_count} người được phân bổ."
            )

    # Validate captain (nếu cập nhật)
    if data.captain_id:
        captain = db.query(User).filter(User.id == data.captain_id).first()
        if not captain:
            raise NotFoundException(detail="Không tìm thấy Trưởng xe")

    # Lưu old data
    old_data = {
        'vehicle_name': vehicle.vehicle_name,
        'route_type': vehicle.route_type,
        'capacity': vehicle.capacity,
        'captain_id': vehicle.captain_id
    }

    # Update
    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)

    # Audit log
    audit_svc.log_action(
        db=db,
        user_id=current_user['sub'],
        emp_code=current_user['emp_code'],
        action="UPDATE",
        entity_type="VEHICLE",
        entity_id=vehicle.id,
        old_data=old_data,
        new_data={
            'vehicle_name': vehicle.vehicle_name,
            'capacity': vehicle.capacity,
            'captain_id': vehicle.captain_id
        },
        reason="Cập nhật thông tin xe"
    )

    return _map_vehicle_to_response(db, vehicle)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: str,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Xóa xe.

    Không cho phép xóa nếu đã có người được phân bổ.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise NotFoundException(detail="Không tìm thấy xe")

    # Check xem có ai đã được phân bổ chưa
    from app.db.models.register import Registration

    route_field_map = {
        "ROUTE_1": "assigned_vehicle_1_id",
        "ROUTE_2": "assigned_vehicle_2_id",
        "ROUTE_3": "assigned_vehicle_3_id",
        "ROUTE_4": "assigned_vehicle_4_id",
    }

    assign_col = route_field_map.get(vehicle.route_type)
    if assign_col:
        assigned_count = db.query(Registration).filter(
            getattr(Registration, assign_col) == vehicle_id
        ).count()

        if assigned_count > 0:
            raise BadRequestException(
                detail=f"Không thể xóa xe này. Đã có {assigned_count} người được phân bổ. "
                       "Vui lòng hủy phân bổ trước khi xóa."
            )

    # Audit log
    audit_svc.log_action(
        db=db,
        user_id=current_user['sub'],
        emp_code=current_user['emp_code'],
        action="DELETE",
        entity_type="VEHICLE",
        entity_id=vehicle_id,
        old_data={
            'vehicle_name': vehicle.vehicle_name,
            'route_type': vehicle.route_type,
            'capacity': vehicle.capacity
        },
        reason="Xóa xe"
    )

    db.delete(vehicle)
    db.commit()

    return None


def _map_vehicle_to_response(db: Session, vehicle: Vehicle) -> VehicleResponse:
    """Helper function map Vehicle model sang VehicleResponse schema"""
    from app.db.models.register import Registration

    route_field_map = {
        "ROUTE_1": "assigned_vehicle_1_id",
        "ROUTE_2": "assigned_vehicle_2_id",
        "ROUTE_3": "assigned_vehicle_3_id",
        "ROUTE_4": "assigned_vehicle_4_id",
    }

    assign_col = route_field_map.get(vehicle.route_type)
    assigned_count = 0

    if assign_col:
        assigned_count = db.query(Registration).filter(
            getattr(Registration, assign_col) == vehicle.id
        ).count()

    available_capacity = vehicle.capacity - assigned_count

    # Lấy thông tin Trưởng xe
    captain_name = None
    captain_phone = None

    if vehicle.captain_id:
        captain = db.query(User).filter(User.id == vehicle.captain_id).first()
        if captain:
            captain_name = captain.full_name
            captain_phone = captain.phone

    return VehicleResponse(
        id=vehicle.id,
        event_id=vehicle.event_id,
        vehicle_name=vehicle.vehicle_name,
        route_type=vehicle.route_type,
        departure_time=vehicle.departure_time,
        pickup_location=vehicle.pickup_location,
        dropoff_location=vehicle.dropoff_location,
        capacity=vehicle.capacity,
        captain_id=vehicle.captain_id,
        notes=vehicle.notes,
        captain_name=captain_name,
        captain_phone=captain_phone,
        assigned_count=assigned_count,
        available_capacity=available_capacity
    )


# ============================================
# IMPORT EXCEL
# ============================================

@router.post("/import", response_model=dict)
async def import_vehicles_from_excel(
    file: UploadFile = File(...),
    event_id: Optional[str] = None,
    current_user: dict = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Import danh sách xe từ Excel.

    Format Excel:
    | vehicle_name | route_type | departure_time      | pickup_location   | dropoff_location | capacity | captain_emp_code | notes |
    |--------------|------------|---------------------|-------------------|------------------|----------|------------------|-------|
    | Bus 01       | ROUTE_1    | 2026-10-15 06:00:00 | Văn phòng HN      | Sân bay HAN      | 45       | NV001            | Có wifi |
    """
    if not event_id:
        event_id = current_user.get("active_event_id")

    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundException(detail="Sự kiện không tồn tại")

    # Đọc Excel
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        print(f"📊 Excel file loaded: {len(df)} rows")
    except Exception as e:
        raise BadRequestException(detail=f"Không thể đọc file Excel: {str(e)}")

    # Validate columns
    required_columns = [
        'vehicle_name', 'route_type', 'departure_time',
        'pickup_location', 'capacity'
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise BadRequestException(
            detail=f"File Excel thiếu các cột: {', '.join(missing_columns)}"
        )

    success_count = 0
    error_count = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            departure_time = pd.to_datetime(row['departure_time'])

            # Tìm captain (nếu có)
            captain_id = None
            if 'captain_emp_code' in row and pd.notna(row['captain_emp_code']):
                captain = db.query(User).filter(
                    User.emp_code == str(row['captain_emp_code'])
                ).first()
                if captain:
                    captain_id = captain.id

            # Check duplicate
            existing = db.query(Vehicle).filter(
                Vehicle.event_id == event_id,
                Vehicle.route_type == str(row['route_type']),
                Vehicle.vehicle_name == str(row['vehicle_name'])
            ).first()

            if existing:
                # Update
                existing.departure_time = departure_time
                existing.pickup_location = str(row['pickup_location'])
                existing.dropoff_location = str(row.get('dropoff_location', ''))
                existing.capacity = int(row['capacity'])
                existing.captain_id = captain_id
                existing.notes = str(row.get('notes', ''))
            else:
                # Tạo mới
                new_vehicle = Vehicle(
                    event_id=event_id,
                    vehicle_name=str(row['vehicle_name']),
                    route_type=str(row['route_type']),
                    departure_time=departure_time,
                    pickup_location=str(row['pickup_location']),
                    dropoff_location=str(row.get('dropoff_location', '')),
                    capacity=int(row['capacity']),
                    captain_id=captain_id,
                    notes=str(row.get('notes', ''))
                )
                db.add(new_vehicle)

            success_count += 1

        except Exception as e:
            errors.append(f"Row {idx + 2}: {str(e)}")
            error_count += 1

    db.commit()

    # Audit log
    audit_svc.log_action(
        db=db,
        user_id=current_user['sub'],
        emp_code=current_user['emp_code'],
        action="IMPORT",
        entity_type="VEHICLE",
        entity_id=event_id,
        new_data={
            'total_rows': len(df),
            'success_count': success_count,
            'error_count': error_count
        },
        reason=f"Import {success_count} xe từ Excel"
    )

    return {
        "success": True,
        "total_rows": len(df),
        "success_count": success_count,
        "error_count": error_count,
        "errors": errors if error_count > 0 else [],
        "message": f"Import hoàn tất: {success_count} thành công, {error_count} lỗi"
    }


@router.get("/export-template")
async def export_vehicles_template(
    current_user: dict = Depends(require_admin_role)
):
    """[ADMIN ONLY] Download template Excel để import xe"""
    template_data = {
        'vehicle_name': ['Bus 01', 'Bus 02', 'Xe 15 chỗ A'],
        'route_type': ['ROUTE_1', 'ROUTE_2', 'ROUTE_1'],
        'departure_time': ['2026-10-15 06:00:00', '2026-10-15 10:30:00', '2026-10-15 06:00:00'],
        'pickup_location': ['Văn phòng HN', 'Sân bay DAD', 'Văn phòng HCM'],
        'dropoff_location': ['Sân bay HAN', 'Khách sạn Sunrise', 'Sân bay SGN'],
        'capacity': [45, 45, 15],
        'captain_emp_code': ['NV001', 'NV002', 'NV003'],
        'notes': ['Có wifi', 'Có nước uống', '']
    }

    df = pd.DataFrame(template_data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Vehicles')

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=vehicle_import_template.xlsx"
        }
    )
