import bcrypt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings

def _get_prehashed_password(password: str) -> bytes:
    """
    Băm mật khẩu bằng SHA-256 trước khi đưa vào bcrypt.
    Việc này tạo ra chuỗi hex 64 ký tự, giải quyết triệt để 
    giới hạn 72 byte của bcrypt đối với các mật khẩu siêu dài.
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest().encode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against hashed password"""
    prehashed = _get_prehashed_password(plain_password)
    # bcrypt yêu cầu dữ liệu phải ở dạng bytes
    return bcrypt.checkpw(prehashed, hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password"""
    prehashed = _get_prehashed_password(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(prehashed, salt)
    return hashed.decode('utf-8')


def create_access_token(
        sub: str,
        emp_code: str,
        team_id: Optional[str],
        active_event_id: Optional[str],
        roles: list
) -> str:
    """
    Tạo Access Token (JWT).

    Thời gian sống: 30 phút (ngắn vì lý do bảo mật)
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": sub,
        "emp_code": emp_code,
        "team_id": team_id,
        "active_event_id": active_event_id,
        "roles": roles,
        "exp": expire,
        "type": "access"  # ✅ Đánh dấu loại token
    }

    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token() -> str:
    """
    Tạo Refresh Token (random string).

    Không dùng JWT vì:
    - Cần lưu vào DB để có thể revoke
    - Không cần payload phức tạp
    """
    return secrets.token_urlsafe(64)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode và verify Access Token.

    Returns:
        dict: JWT payload nếu token hợp lệ
        None: Nếu token invalid hoặc expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # ✅ Kiểm tra loại token
        if payload.get("type") != "access":
            return None

        return payload
    except JWTError:
        return None