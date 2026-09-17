"""
Database Seeding Script

Tạo dữ liệu mặc định cho hệ thống:
- Admin user đầu tiên
- Event mẫu (nếu cần)
- Teams mẫu (nếu cần)
"""

from sqlalchemy.orm import Session
from app.db.models.user import User, Team
from app.db.models.event import Event
from app.core.security import get_password_hash
from datetime import datetime, timedelta


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
        hashed_password=get_password_hash("Admin@123456"),
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

    print(f"✅ Đã tạo tài khoản Admin: {admin_user.email}")
    print(f"   📧 Email: admin@company.com")
    print(f"   🔑 Password: Admin@123456")
    print(f"   ⚠️  Vui lòng đổi mật khẩu sau khi đăng nhập lần đầu!")

    return admin_user


def seed_sample_event(db: Session) -> Event:
    """
    Tạo sự kiện mẫu để test.

    Chỉ dùng trong môi trường Development.
    """
    # Kiểm tra xem đã có event nào chưa
    existing_event = db.query(Event).first()

    if existing_event:
        print(f"✅ Event đã tồn tại: {existing_event.name}")
        return existing_event

    # Tạo event mẫu
    sample_event = Event(
        name="Team Building Da Nang 2026",
        status="DRAFT",
        start_date=datetime.now() + timedelta(days=30),
        end_date=datetime.now() + timedelta(days=32),
        location="Da Nang",
        registration_deadline=datetime.now() + timedelta(days=15),
        description="Chuyến đi team building hàng năm tại Đà Nẵng. Khám phá bãi biển đẹp và văn hóa địa phương."
    )

    db.add(sample_event)
    db.commit()
    db.refresh(sample_event)

    print(f"✅ Đã tạo Event mẫu: {sample_event.name} (ID: {sample_event.id})")

    return sample_event


def seed_sample_teams(db: Session, event_id: str):
    """
    Tạo các team mẫu.
    """
    team_names = [
        "AI Development Team",
        "Backend Team",
        "Frontend Team",
        "DevOps Team",
        "QA Team",
        "Product Team"
    ]

    existing_teams = db.query(Team).filter(Team.event_id == event_id).count()

    if existing_teams > 0:
        print(f"✅ Đã có {existing_teams} teams trong event")
        return

    for team_name in team_names:
        team = Team(
            name=team_name,
            event_id=event_id
        )
        db.add(team)

    db.commit()
    print(f"✅ Đã tạo {len(team_names)} teams mẫu")


def seed_sample_users(db: Session, team_id: str):
    """
    Tạo users mẫu cho testing.
    """
    sample_users = [
        {
            "emp_code": "NV001",
            "full_name": "Nguyen Van A",
            "email": "nva@company.com",
            "password": "123456",
            "roles": "USER",
            "is_representative": True  # Đại diện team
        },
        {
            "emp_code": "NV002",
            "full_name": "Tran Thi B",
            "email": "ttb@company.com",
            "password": "123456",
            "roles": "USER",
            "is_representative": False
        },
        {
            "emp_code": "NV003",
            "full_name": "Le Van C",
            "email": "lvc@company.com",
            "password": "123456",
            "roles": "USER",
            "is_representative": False
        }
    ]

    for user_data in sample_users:
        # Check duplicate
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            continue

        user = User(
            emp_code=user_data["emp_code"],
            full_name=user_data["full_name"],
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            phone="+84901234567",
            work_location="HN Office",
            team_id=team_id,
            roles=user_data["roles"],
            is_representative=user_data["is_representative"],
            is_priority=False
        )
        db.add(user)

    db.commit()
    print(f"✅ Đã tạo {len(sample_users)} users mẫu")


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

    # 2. Tạo event mẫu (development mode)
    if mode == "development":
        event = seed_sample_event(db)
        seed_sample_teams(db, event.id)

        # Lấy team đầu tiên để gán users
        first_team = db.query(Team).filter(Team.event_id == event.id).first()
        if first_team:
            seed_sample_users(db, first_team.id)

    print("=" * 60)
    print("✅ Seed hoàn tất!")
    print("=" * 60)
