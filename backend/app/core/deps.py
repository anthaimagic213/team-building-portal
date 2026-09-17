from typing import Generator, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.db.session import get_db

# OAuth2 scheme cho JWT token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Extract và validate current user từ JWT token.

    Returns JWT payload chứa:
    - sub: User UUID
    - emp_code: Employee code
    - team_id: Team UUID
    - active_event_id: Current event UUID
    - roles: List of roles (USER, ADMIN, TEAM_REPRESENTATIVE)

    Throws:
    - 401 Unauthorized: Token invalid hoặc expired
    """
    payload = decode_access_token(token)

    if payload is None:
        raise UnauthorizedException(
            detail="Token không hợp lệ hoặc đã hết hạn"
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException(detail="Token không chứa thông tin user")

    return payload


def require_roles(required_roles: List[str]):
    """
    Dependency factory để yêu cầu một hoặc nhiều roles.

    Usage:
        @router.get("/admin/something")
        async def admin_only(current_user: dict = Depends(require_roles(["ADMIN"]))):
            ...

    Args:
        required_roles: Danh sách roles được phép (OR logic)

    Returns:
        Dependency function kiểm tra roles

    Throws:
        403 Forbidden: User không có role phù hợp
    """

    async def _check_roles(current_user: dict = Depends(get_current_user)) -> dict:
        user_roles = current_user.get("roles", [])

        # Kiểm tra xem user có ít nhất 1 role trong required_roles không
        has_required_role = any(role in user_roles for role in required_roles)

        if not has_required_role:
            raise ForbiddenException(
                detail=f"Yêu cầu một trong các quyền: {', '.join(required_roles)}"
            )

        return current_user

    return _check_roles


def require_admin_role(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency để yêu cầu ADMIN role.

    Chỉ có BTC (Ban Tổ Chức) mới có quyền này.

    Usage:
        @router.post("/admin/events")
        async def create_event(current_user: dict = Depends(require_admin_role)):
            ...

    Throws:
        403 Forbidden: User không có role ADMIN
    """
    roles = current_user.get("roles", [])
    if "ADMIN" not in roles:
        raise ForbiddenException(
            detail="Chỉ có Ban Tổ Chức (ADMIN) mới có quyền thực hiện thao tác này"
        )
    return current_user


def require_team_representative(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency để yêu cầu TEAM_REPRESENTATIVE role.

    Dùng cho:
    - Chọn ghế Gala Dinner (đại diện team)
    - Các thao tác cấp team khác

    Note: ADMIN cũng được phép (vì BTC có thể can thiệp)

    Throws:
        403 Forbidden: User không có role TEAM_REPRESENTATIVE hoặc ADMIN
    """
    roles = current_user.get("roles", [])
    if "TEAM_REPRESENTATIVE" not in roles and "ADMIN" not in roles:
        raise ForbiddenException(
            detail="Chỉ có Đại diện Team hoặc Ban Tổ Chức mới có quyền này"
        )
    return current_user


def require_any_auth(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency để yêu cầu user đã đăng nhập (bất kỳ role nào).

    Dùng cho:
    - Đăng ký Team Building
    - Xem My Journey
    - Các endpoint user thông thường

    Usage:
        @router.get("/registrations/me")
        async def my_registration(current_user: dict = Depends(require_any_auth)):
            ...
    """
    # get_current_user đã validate token
    # Chỉ cần return payload
    return current_user
