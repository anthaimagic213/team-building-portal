from sqlalchemy.orm import Session
from app.core.security import (
    verify_password,
    create_access_token,
    get_password_hash
)
from app.core.exceptions import UnauthorizedException, ConflictException
from app.db.models.user import User
from app.db.models.event import Event
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate
from app.services import token_svc
from typing import Optional


def authenticate_user(
        db: Session,
        credentials: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
) -> TokenResponse:
    """
    Xử lý logic đăng nhập và cấp phát JWT Token + Refresh Token.

    Args:
        db: Database session
        credentials: Login credentials
        ip_address: Client IP
        user_agent: Client user agent

    Returns:
        TokenResponse với access_token và refresh_token
    """
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise UnauthorizedException(detail="Email hoặc mật khẩu không chính xác")

    # Lấy sự kiện đang active
    active_event = db.query(Event).order_by(Event.created_at.desc()).first()

    # Xử lý Roles (RBAC)
    roles = user.roles.split(",") if user.roles else ["USER"]
    if user.is_representative and "TEAM_REPRESENTATIVE" not in roles:
        roles.append("TEAM_REPRESENTATIVE")

    # ✅ Tạo Access Token (JWT)
    access_token = create_access_token(
        sub=user.id,
        emp_code=user.emp_code,
        team_id=user.team_id,
        active_event_id=active_event.id if active_event else None,
        roles=roles
    )

    # ✅ Tạo Refresh Token
    refresh_token_obj = token_svc.create_refresh_token_for_user(
        db=db,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_obj.plain_token,  # ✅ Trả về plain token
        token_type="bearer",
        user_id=user.id,
        emp_code=user.emp_code,
        full_name=user.full_name,
        roles=roles
    )


def register_new_user(db: Session, user_in: UserCreate) -> User:
    """Xử lý logic tạo tài khoản mới"""
    if db.query(User).filter(User.email == user_in.email).first():
        raise ConflictException(detail="Email này đã được sử dụng")

    if db.query(User).filter(User.emp_code == user_in.emp_code).first():
        raise ConflictException(detail="Mã nhân viên này đã tồn tại")

    new_user = User(
        emp_code=user_in.emp_code,
        full_name=user_in.full_name,
        email=user_in.email,
        phone=user_in.phone,
        work_location=user_in.work_location,
        team_id=user_in.team_id,
        hashed_password=get_password_hash(user_in.password),
        roles="USER",
        is_representative=user_in.is_representative,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
