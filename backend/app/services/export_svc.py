import pandas as pd
from io import BytesIO
from sqlalchemy.orm import Session
from app.db.models import Registration, User, Event, Flight, Vehicle, GalaSeat


def export_registrations_to_excel(db: Session, event_id: str) -> BytesIO:
    """Query toàn bộ dữ liệu SSOT và xuất file Excel dạng Bytes"""

    # Query join nhiều bảng để lấy data tổng hợp
    regs = db.query(Registration).filter(Registration.event_id == event_id).all()

    data = []
    for reg in regs:
        user = reg.user
        flight = reg.flight
        v1, v2, v3, v4 = reg.vehicle_1, reg.vehicle_2, reg.vehicle_3, reg.vehicle_4

        # Lấy ghế Gala nếu có
        gala_seat = db.query(GalaSeat).filter(
            GalaSeat.locked_by_team_id == user.team_id,
            GalaSeat.status == "CONFIRMED"
        ).first() if user.team_id else None

        row = {
            "Mã NV": user.emp_code,
            "Họ tên": user.full_name,
            "Email": user.email,
            "Team": user.team.name if user.team else "N/A",
            "Tham gia": "Có" if reg.is_participating else "Không",
            "Ca nguyện vọng": "Ca 1" if reg.desired_shift == "SHIFT_1" else (
                "Ca 2" if reg.desired_shift == "SHIFT_2" else ""),
            "Mã chuyến bay": flight.flight_code if flight else "",
            "Xe chặng 1 (HN-SB)": v1.vehicle_name if v1 else ("Cần xe" if reg.need_vehicle_route_1 else "Tự túc"),
            "Xe chặng 2 (SB-KS)": v2.vehicle_name if v2 else ("Cần xe" if reg.need_vehicle_route_2 else "Tự túc"),
            "Xe chặng 3 (KS-SB)": v3.vehicle_name if v3 else ("Cần xe" if reg.need_vehicle_route_3 else "Tự túc"),
            "Xe chặng 4 (SB-HN)": v4.vehicle_name if v4 else ("Cần xe" if reg.need_vehicle_route_4 else "Tự túc"),
            "Phòng KS": reg.assigned_hotel_room or "",
            "Ghế Gala": gala_seat.seat_code if gala_seat else "",
            "Ghi chú": reg.wishes or ""
        }
        data.append(row)

    df = pd.DataFrame(data)

    # Ghi ra bộ nhớ đệm (BytesIO) để trả thẳng về HTTP Response, không lưu ổ cứng
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Danh_sach_dang_ky')

    output.seek(0)
    return output