"""
Admin Hotel Management Endpoints

BTC quản lý khách sạn và import phân phòng.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
from io import BytesIO
from app.core.deps import require_admin_role
from app.db.session import get_db
from app.db.models.hotel import Hotel, HotelRoom
from app.db.models.user import User
from app.db.models.register import Registration
from app.db.models.event import Event
from app.core.exceptions import NotFoundException, BadRequestException
from app.services import audit_svc

router = APIRouter()


@router.post("/import-rooms", response_model=dict)
async def import_hotel_rooms_from_excel(
        file: UploadFile = File(...),
        event_id: str = None,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Import phân phòng khách sạn từ Excel.

    Format Excel yêu cầu:
    | hotel_name | room_code | room_type | emp_code_1 | emp_code_2 | emp_code_3 |
    |------------|-----------|-----------|------------|------------|------------|
    | Hotel A    | A101      | Double    | NV001      | NV002      |            |
    | Hotel A    | A102      | Single    | NV003      |            |            |

    Returns:
        Summary: số phòng import thành công, số lỗi
    """
    if not event_id:
        event_id = current_user.get("active_event_id")

    if not event_id:
        raise NotFoundException(detail="Không tìm thấy sự kiện")

    # Validate event
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundException(detail="Sự kiện không tồn tại")

    # Đọc Excel
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        df.columns = [str(column).strip().lower() for column in df.columns]
        print(f"📊 Excel file loaded: {len(df)} rows")
    except Exception as e:
        raise BadRequestException(detail=f"Không thể đọc file Excel: {str(e)}")

    # Validate columns
    required_columns = ['hotel_name', 'room_code']
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
            hotel_name = str(row['hotel_name']).strip()
            room_code = str(row['room_code']).strip()
            room_type_value = row.get('room_type', 'Standard')
            room_type = str(room_type_value).strip() if pd.notna(room_type_value) else 'Standard'

            # Tìm hoặc tạo hotel
            hotel = db.query(Hotel).filter(
                Hotel.event_id == event_id,
                Hotel.hotel_name == hotel_name
            ).first()

            if not hotel:
                hotel = Hotel(
                    event_id=event_id,
                    hotel_name=hotel_name,
                    total_rooms=0
                )
                db.add(hotel)
                db.flush()

            # Lấy danh sách emp_codes
            emp_codes = []
            for i in range(1, 10):  # Hỗ trợ tối đa 9 người/phòng
                col_name = f'emp_code_{i}'
                if col_name in row and pd.notna(row[col_name]):
                    emp_codes.append(str(row[col_name]).strip())

            # Tìm user_ids từ emp_codes
            user_ids = []
            for emp_code in emp_codes:
                user = db.query(User).filter(User.emp_code == emp_code).first()
                if user:
                    user_ids.append(user.id)
                else:
                    errors.append(f"Row {idx + 2}: Không tìm thấy user với mã {emp_code}")

            # Tạo hoặc update room
            room = db.query(HotelRoom).filter(
                HotelRoom.hotel_id == hotel.id,
                HotelRoom.room_code == room_code
            ).first()

            if room:
                # Update
                room.room_type = room_type
                room.capacity = len(user_ids)
                room.assigned_user_ids = ','.join(user_ids) if user_ids else None
            else:
                # Tạo mới
                room = HotelRoom(
                    hotel_id=hotel.id,
                    room_code=room_code,
                    room_type=room_type,
                    capacity=len(user_ids),
                    assigned_user_ids=','.join(user_ids) if user_ids else None
                )
                db.add(room)
                hotel.total_rooms += 1

            # Cập nhật assigned_hotel_room cho registrations
            for user_id in user_ids:
                reg = db.query(Registration).filter(
                    Registration.user_id == user_id,
                    Registration.event_id == event_id
                ).first()

                if reg:
                    reg.assigned_hotel_room = room_code

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
        entity_type="HOTEL_ROOMS",
        entity_id=event_id,
        new_data={'imported_rooms': success_count},
        reason="Import phân phòng từ Excel"
    )

    return {
        "success": True,
        "total_rows": len(df),
        "success_count": success_count,
        "error_count": error_count,
        "errors": errors if error_count > 0 else [],
        "message": f"Import hoàn tất: {success_count} phòng, {error_count} lỗi"
    }


@router.get("/export-template")
async def export_hotel_rooms_template(
        current_user: dict = Depends(require_admin_role)
):
    """Download template Excel để import phân phòng"""
    from fastapi.responses import StreamingResponse
    import io

    template_data = {
        'hotel_name': ['Hotel Sunrise', 'Hotel Sunrise', 'Hotel Sunset'],
        'room_code': ['A101', 'A102', 'B201'],
        'room_type': ['Double', 'Single', 'Suite'],
        'emp_code_1': ['NV001', 'NV003', 'NV005'],
        'emp_code_2': ['NV002', '', 'NV006'],
        'emp_code_3': ['', '', 'NV007']
    }

    df = pd.DataFrame(template_data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Hotel Rooms')

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=hotel_rooms_template.xlsx"
        }
    )


@router.get("", response_model=List[dict])
async def list_hotels(
        event_id: str = None,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db)
):
    """[ADMIN ONLY] Lấy danh sách khách sạn và phòng"""
    if not event_id:
        event_id = current_user.get("active_event_id")

    hotels = db.query(Hotel).filter(Hotel.event_id == event_id).all()

    result = []
    for hotel in hotels:
        rooms = db.query(HotelRoom).filter(HotelRoom.hotel_id == hotel.id).all()

        result.append({
            "id": hotel.id,
            "hotel_name": hotel.hotel_name,
            "address": hotel.address,
            "total_rooms": hotel.total_rooms,
            "rooms": [
                {
                    "id": room.id,
                    "room_code": room.room_code,
                    "room_type": room.room_type,
                    "capacity": room.capacity,
                    "assigned_count": len(room.assigned_user_ids.split(',')) if room.assigned_user_ids else 0
                }
                for room in rooms
            ]
        })

    return result
