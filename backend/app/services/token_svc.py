"""
Refresh Token Service

Quản lý vòng đời của Refresh Token:
- Tạo refresh token mới
- Validate refresh token
- Revoke (thu hồi) refresh token
- Cleanup expired tokens
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.models.user import RefreshToken, User
from app.core.security import create_refresh_token, get_password_hash
from app.core.config import settings
from typing import Optional


def create_refresh_token_for_user(
        db: Session,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
) -> RefreshToken:
    """
    Tạo Refresh Token mới cho user.

    Args:
        db: Database session
        user_id: User UUID
        ip_address: IP address của client
        user_agent: User agent string

    Returns:
        RefreshToken object
    """
    # Tạo token string
    token_string = create_refresh_token()

    # Hash token trước khi lưu DB (bảo mật)
    hashed_token = get_password_hash(token_string)

    # Tính expiry
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Tạo record
    refresh_token = RefreshToken(
        user_id=user_id,
        token=hashed_token,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent
    )

    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)

    # ⚠️ Return plain token (chỉ lần này, không lưu lại)
    # Frontend sẽ lưu plain token này
    refresh_token.plain_token = token_string

    return refresh_token


def validate_refresh_token(
        db: Session,
        token_string: str
) -> Optional[RefreshToken]:
    """
    Validate refresh token.

    Kiểm tra:
    1. Token có tồn tại trong DB không
    2. Token có bị revoke không
    3. Token có hết hạn không

    Args:
        db: Database session
        token_string: Plain refresh token string

    Returns:
        RefreshToken object nếu hợp lệ, None nếu không hợp lệ
    """
    # Tìm tất cả refresh tokens (vì token đã được hash)
    all_tokens = db.query(RefreshToken).filter(
        RefreshToken.is_revoked == False
    ).all()

    # So sánh hash
    from app.core.security import verify_password
    for rt in all_tokens:
        if verify_password(token_string, rt.token):
            # Kiểm tra expiry
            if rt.expires_at < datetime.utcnow():
                return None  # Token đã hết hạn

            return rt

    return None


def revoke_refresh_token(
        db: Session,
        token_id: str
) -> bool:
    """
    Thu hồi (revoke) refresh token.

    Use case:
    - User logout
    - Admin force logout
    - Security incident

    Args:
        db: Database session
        token_id: RefreshToken UUID

    Returns:
        True if success, False if not found
    """
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.id == token_id
    ).first()

    if not refresh_token:
        return False

    refresh_token.is_revoked = True
    refresh_token.revoked_at = datetime.utcnow()

    db.commit()

    return True


def revoke_all_user_tokens(
        db: Session,
        user_id: str
) -> int:
    """
    Thu hồi TẤT CẢ refresh tokens của một user.

    Use case:
    - User đổi mật khẩu
    - Security incident
    - Admin force logout all devices

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        Number of tokens revoked
    """
    result = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False
    ).update({
        "is_revoked": True,
        "revoked_at": datetime.utcnow()
    })

    db.commit()

    return result


def cleanup_expired_tokens(db: Session) -> int:
    """
    Xóa các refresh tokens đã hết hạn (cleanup job).

    Nên chạy định kỳ (VD: mỗi ngày lúc 2 AM)

    Args:
        db: Database session

    Returns:
        Number of tokens deleted
    """
    result = db.query(RefreshToken).filter(
        RefreshToken.expires_at < datetime.utcnow()
    ).delete()

    db.commit()

    return result
