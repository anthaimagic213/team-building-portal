"""Seed dữ liệu mặc định và dữ liệu mẫu cho môi trường kiểm thử.

Chạy từ thư mục ``backend`` bằng ``python seed_dev.py --full``.
Seed idempotent: chạy nhiều lần không tạo bản ghi trùng và không xóa dữ liệu.
Full seed gồm 4 event, 32 team và 320 CBNV mẫu.
"""

from sqlalchemy.orm import Session
from app.db.models.user import User, Team
from app.db.models.event import Event
from app.core.security import get_password_hash
from datetime import datetime, timedelta


DEFAULT_ADMIN_PASSWORD = "Admin@123456"
SAMPLE_USER_PASSWORD = "Test@123456"


def seed_admin_user(db: Session) -> User:
    """
    Tạo tài khoản ADMIN mặc định.

    Credentials:
    - Email: admin@company.com
    - Password: Admin@123456
    - Role: ADMIN

    ⚠️ QUAN TRỌNG: Phải đổi mật khẩu này trong production!
    """
    # Kiểm tra xem đã có admin chưa
    existing_admin = db.query(User).filter(
        User.roles.like("%ADMIN%")
    ).first()

    if existing_admin:
        print(f"✅ Admin đã tồn tại: {existing_admin.email}")
        return existing_admin

    # Tạo admin mới
    admin_user = User(
        emp_code="ADMIN001",
        full_name="System Administrator",
        email="admin@company.com",
        hashed_password=get_password_hash(DEFAULT_ADMIN_PASSWORD),
        phone="+84901234567",
        work_location="Head Office",
        team_id=None,
        roles="ADMIN,USER",  # Admin cũng có role USER
        is_representative=False,
        is_priority=True
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    print("✅ Đã tạo admin: admin@company.com / Admin@123456")

    return admin_user


EVENTS = [
    ("Team Building Da Nang 2026", "Da Nang", "REGISTRATION_OPEN"),
    ("Company Trip Nha Trang 2026", "Nha Trang", "DRAFT"),
    ("Annual Retreat Phu Quoc 2026", "Phu Quoc", "DRAFT"),
    ("Team Building Ha Long 2027", "Ha Long", "DRAFT"),
]

TEAM_NAMES = ["Engineering", "Product", "Sales", "Marketing", "Finance", "Human Resources", "Customer Success", "Operations"]
FIRST_NAMES = ["Nguyen Van", "Tran Thi", "Le Hoang", "Pham Minh", "Vo Thanh", "Bui Ngoc", "Dang Quoc", "Doan Thu", "Hoang Anh", "Phan Gia"]
def seed_sample_data(db: Session) -> tuple[int, int, int]:
    """Tạo 4 events, 32 teams và 320 CBNV mẫu, không trùng dữ liệu."""
    now = datetime.now()
    created = [0, 0, 0]
    for event_index, (event_name, location, status) in enumerate(EVENTS, 1):
        event = db.query(Event).filter(Event.name == event_name).first()
        if event is None:
            event = Event(name=event_name, status=status,
                          start_date=now + timedelta(days=30 * event_index),
                          end_date=now + timedelta(days=30 * event_index + 2),
                          location=location,
                          registration_deadline=now + timedelta(days=30 * event_index - 10),
                          description=f"Dữ liệu mẫu kiểm thử tại {location}.")
            db.add(event)
            db.flush()
            created[0] += 1
        for team_index, team_name in enumerate(TEAM_NAMES, 1):
            full_team_name = f"E{event_index:02d} - {team_name}"
            team = db.query(Team).filter(Team.name == full_team_name).first()
            if team is None:
                team = Team(name=full_team_name, event_id=event.id)
                db.add(team)
                db.flush()
                created[1] += 1
            for member_index in range(1, 11):
                emp_code = f"E{event_index:02d}T{team_index:02d}{member_index:02d}"
                if db.query(User).filter(User.emp_code == emp_code).first():
                    continue
                db.add(User(emp_code=emp_code,
                            full_name=f"{FIRST_NAMES[member_index - 1]} {event_index}{team_index:02d}{member_index:02d}",
                            email=f"{emp_code.lower()}@company.com",
                            hashed_password=get_password_hash(SAMPLE_USER_PASSWORD),
                            phone=f"+8490{event_index:02d}{team_index:02d}{member_index:02d}00",
                            work_location=location, team_id=team.id, roles="USER",
                            is_representative=member_index == 1, is_priority=member_index <= 2))
                created[2] += 1
    db.commit()
    return tuple(created)
def run_seed(db: Session, mode: str = "minimal"):
    """
    Chạy seed data.

    Modes:
    - minimal: Chỉ tạo admin
    - development: Tạo admin + event + teams + users mẫu
    - production: Chỉ tạo admin (nếu chưa có)
    """
    print("=" * 60)
    print(f"🌱 SEEDING DATABASE - Mode: {mode}")
    print("=" * 60)

    # 1. Tạo admin (bắt buộc)
    admin = seed_admin_user(db)

    if mode == "minimal":
        print("=" * 60)
        print("✅ Seed hoàn tất (minimal mode)")
        print("=" * 60)
        return

    if mode == "development":
        event_count, team_count, user_count = seed_sample_data(db)
        print(f"✅ Đã tạo mới: {event_count} events, {team_count} teams, {user_count} CBNV")
        print(f"🔑 Mật khẩu CBNV mẫu: {SAMPLE_USER_PASSWORD}")
    else:
        print("ℹ️ Minimal mode: chỉ seed admin")
    print("✅ Seed hoàn tất!")
