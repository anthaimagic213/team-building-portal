from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class LoginRequest(BaseModel):
    """Schema for user login request"""
    email: EmailStr = Field(..., description="User's corporate email address")
    password: str = Field(..., min_length=6, description="User password")


class TokenResponse(BaseModel):
    """
    JWT Token response with Refresh Token.

    - access_token: Short-lived JWT (30 minutes)
    - refresh_token: Long-lived token (30 days) để lấy access token mới
    """
    access_token: str = Field(..., description="JWT access token (30 phút)")
    refresh_token: str = Field(..., description="Refresh token (30 ngày)")  # ✅ THÊM
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    user_id: str = Field(..., description="User UUID")
    emp_code: str = Field(..., description="Employee code")
    full_name: str = Field(..., description="User's full name")
    roles: List[str] = Field(..., description="User roles: USER, ADMIN, TEAM_REPRESENTATIVE")


class RefreshTokenRequest(BaseModel):
    """Request để lấy access token mới từ refresh token"""
    refresh_token: str = Field(..., description="Refresh token đã lưu từ lúc login")


class JWTPayload(BaseModel):
    """JWT Payload structure"""
    sub: str = Field(..., description="User UUID - primary identifier")
    emp_code: str = Field(..., description="Employee code")
    team_id: Optional[str] = Field(None, description="Team UUID")
    active_event_id: Optional[str] = Field(None, description="Active event UUID")
    roles: List[str] = Field(default_factory=list, description="User roles")
    exp: int = Field(..., description="Token expiration timestamp (Unix epoch)")
    type: str = Field(default="access", description="Token type: access or refresh")
