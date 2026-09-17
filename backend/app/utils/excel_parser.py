import pandas as pd
from typing import List, Dict
from io import BytesIO
from sqlalchemy.orm import Session
from app.db.models import Registration, User


def parse_hotel_allocations(file_bytes: bytes, db: Session, event_id: str) -> Dict:
    """
    Đọc file Excel phân phòng từ BTC và mapping vào hệ thống.
    Yêu cầu file Excel có 2 cột: 'emp_code' và 'room_number'.
    """
    try:
        # Sử dụng BytesIO để pandas đọc trực tiếp file từ memory (không cần lưu tạm xuống ổ cứng)
        df = pd.read_excel(BytesIO(file_bytes), dtype=str)

        # Tiền xử lý: Xóa khoảng trắng thừa ở tên cột
        df.columns = df.columns.str.strip().str.lower()

        if 'emp_code' not in df.columns or 'room_number' not in df.columns:
            return {"success": False, "message": "File Excel thiếu cột 'emp_code' hoặc 'room_number'."}

        success_count = 0
        error_logs = []

        # Duyệt từng dòng trong Excel
        for index, row in df.iterrows():
            emp_code = str(row['emp_code']).strip()
            room_number = str(row['room_number']).strip()

            # Tìm User_id thông qua mã nhân viên
            user = db.query(User).filter(User.emp_code == emp_code).first()
            if not user:
                error_logs.append(f"Dòng {index + 2}: Mã nhân viên {emp_code} không tồn tại.")
                continue

            # Cập nhật mã phòng vào bảng Đăng ký
            reg = db.query(Registration).filter(
                Registration.user_id == user.id,
                Registration.event_id == event_id
            ).first()

            if not reg:
                error_logs.append(f"Dòng {index + 2}: Nhân viên {emp_code} chưa đăng ký sự kiện này.")
                continue

            reg.assigned_hotel_room = room_number
            success_count += 1

        db.commit()

        return {
            "success": True,
            "total_processed": len(df),
            "success_count": success_count,
            "error_logs": error_logs
        }

    except Exception as e:
        return {"success": False, "message": f"Lỗi đọc file Excel: {str(e)}"}