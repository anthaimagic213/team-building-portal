from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest
from app.schemas.user import UserCreate, UserResponse
from app.services import auth_svc, token_svc
from app.db.models.user import User
from app.core.security import (
    get_password_hash,
    create_access_token
)
from app.db.models.event import Event

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
        credentials: LoginRequest,
        request: Request,
        db: Session = Depends(get_db)
):
    """
    Xác thực người dùng và cấp phát JWT Token + Refresh Token.

    Returns:
    - access_token: Dùng cho mọi API request (30 phút)
    - refresh_token: Dùng để lấy access_token mới (30 ngày)
    """
    # Lấy IP và User Agent
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    return auth_svc.authenticate_user(
        db,
        credentials,
        ip_address=ip_address,
        user_agent=user_agent
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
        data: RefreshTokenRequest,
        db: Session = Depends(get_db)
):
    """
    ✅ Lấy Access Token mới từ Refresh Token.

    Flow:
    1. Frontend gửi refresh_token
    2. Backend validate refresh_token
    3. Nếu hợp lệ → Tạo access_token mới
    4. Trả về access_token mới (không tạo refresh_token mới)

    Use case:
    - Access token hết hạn (401)
    - Frontend tự động gọi endpoint này để lấy token mới
    """
    # Validate refresh token
    refresh_token_obj = token_svc.validate_refresh_token(db, data.refresh_token)

    if not refresh_token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại."
        )

    # Lấy user info
    user = db.query(User).filter(User.id == refresh_token_obj.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User không tồn tại"
        )

    # Lấy active event
    active_event = db.query(Event).order_by(Event.created_at.desc()).first()

    # Xử lý roles
    roles = user.roles.split(",") if user.roles else ["USER"]
    if user.is_representative and "TEAM_REPRESENTATIVE" not in roles:
        roles.append("TEAM_REPRESENTATIVE")

    # ✅ Tạo Access Token mới
    new_access_token = create_access_token(
        sub=user.id,
        emp_code=user.emp_code,
        team_id=user.team_id,
        active_event_id=active_event.id if active_event else None,
        roles=roles
    )

    # ✅ Trả về token mới (KHÔNG tạo refresh token mới)
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=data.refresh_token,  # Giữ nguyên refresh token cũ
        token_type="bearer",
        user_id=user.id,
        emp_code=user.emp_code,
        full_name=user.full_name,
        roles=roles
    )


@router.post("/logout")
async def logout(
        data: RefreshTokenRequest,
        db: Session = Depends(get_db)
):
    """
    ✅ Đăng xuất - Revoke refresh token.

    Frontend nên:
    1. Gọi endpoint này
    2. Xóa access_token và refresh_token khỏi localStorage
    3. Redirect về /login
    """
    # Validate và revoke refresh token
    refresh_token_obj = token_svc.validate_refresh_token(db, data.refresh_token)

    if refresh_token_obj:
        token_svc.revoke_refresh_token(db, refresh_token_obj.id)

    return {
        "success": True,
        "message": "Đăng xuất thành công"
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Đăng ký tài khoản mới (Dùng cho môi trường Dev/Test)"""
    user = auth_svc.register_new_user(db, user_in)
    from app.services.registration_svc import send_account_created_email
    background_tasks.add_task(send_account_created_email, user.id, user_in.password)
    return user


@router.post("/bootstrap-admin", response_model=dict, status_code=status.HTTP_201_CREATED)
async def bootstrap_admin(db: Session = Depends(get_db)):
    """Bootstrap Admin Account (chỉ chạy khi chưa có admin)"""
    existing_admin = db.query(User).filter(User.roles.like("%ADMIN%")).first()

    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Hệ thống đã có tài khoản ADMIN"
        )

    admin_user = User(
        emp_code="ADMIN001",
        full_name="System Administrator",
        email="admin@company.com",
        hashed_password=get_password_hash("Admin@123456"),
        phone="+84901234567",
        work_location="Head Office",
        team_id=None,
        roles="ADMIN,USER",
        is_representative=False,
        is_priority=True
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    return {
        "success": True,
        "message": "Tài khoản ADMIN đã được tạo thành công",
        "credentials": {
            "email": "admin@company.com",
            "password": "Admin@123456"
        },
        "warning": "⚠️ VUI LÒNG ĐỔI MẬT KHẨU SAU KHI ĐĂNG NHẬP LẦN ĐẦU!"
    }
