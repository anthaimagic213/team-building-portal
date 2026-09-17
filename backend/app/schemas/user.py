from typing import List, Optional
from datetime import datetime
from pydantic import *


class TeamBase(BaseModel):
    """Base schema for Team"""
    team_name: str = Field(..., description="Team or department name")
    event_id: str = Field(..., description="Associated event UUID")


class TeamCreate(TeamBase):
    """Schema for creating a new team"""
    pass


class TeamUpdate(BaseModel):
    """Schema for updating team information"""
    team_name: str | None = Field(None, description="Updated team name")


class TeamResponse(TeamBase):
    """Team response with full details"""
    id: str = Field(..., description="Team UUID")
    member_count: int = Field(default=0, description="Number of team members")
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    """
    Base schema for User with semantic field descriptions for RAG.
    
    Each field is described clearly so LLM can understand the data model
    when executing tool calls for personalized queries.
    """
    emp_code: str = Field(
        ..., 
        description="Employee code - unique identifier for business operations",
        min_length=1,
        max_length=50
    )
    full_name: str = Field(
        ..., 
        description="Employee's full name",
        min_length=1,
        max_length=200
    )
    email: EmailStr = Field(..., description="Corporate email address")
    phone: str | None = Field(None, description="Contact phone number")
    work_location: str | None = Field(
        None, 
        description="Work location: HN (Hanoi), HCM (Ho Chi Minh), or other configured locations"
    )


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=6, description="User password (will be hashed)")
    team_id: str | None = Field(None, description="Team UUID")
    is_representative: bool = Field(
        default=False,
        description="Whether user is authorized to represent team (e.g., for Gala seat selection)"
    )


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    full_name: str | None = Field(None, description="Updated full name")
    email: EmailStr | None = Field(None, description="Updated email")
    phone: str | None = Field(None, description="Updated phone number")
    work_location: str | None = Field(None, description="Updated work location")
    team_id: str | None = Field(None, description="Updated team assignment")
    is_representative: bool | None = Field(None, description="Updated representative status")


class UserSelfUpdate(BaseModel):
    """Fields a user may update without changing identity or permissions."""
    phone: str | None = Field(None, max_length=50, description="Updated phone number")
    password: str | None = Field(None, min_length=6, description="New password")

    @model_validator(mode="after")
    def require_a_change(self):
        if self.phone is None and self.password is None:
            raise ValueError("Cần cung cấp phone hoặc password để cập nhật")
        return self


class AdminRepresentativeUpdate(BaseModel):
    """Admin-only permission change for Gala representation."""
    event_id: str
    is_representative: bool


class UserResponse(BaseModel):
    id: str
    emp_code: str
    full_name: str
    email: str
    phone: str | None = None
    work_location: str | None = None

    # Khai báo kiểu mảng
    roles: list[str]

    created_at: datetime | None = None

    # Cú pháp chuẩn của Pydantic V2 để đọc dữ liệu từ SQLAlchemy Model
    model_config = {"from_attributes": True}

    # Bắt buộc phải có đoạn này để convert chuỗi "USER" từ DB thành ["USER"]
    @field_validator("roles", mode="before")
    @classmethod
    def parse_roles(cls, v):
        if isinstance(v, str):
            # Cắt chuỗi theo dấu phẩy phòng trường hợp user có nhiều quyền (vd: "USER,ADMIN")
            return [r.strip() for r in v.split(",") if r.strip()]
        return v


class UserListItem(BaseModel):
    """Simplified user info for list views"""
    id: str
    emp_code: str
    full_name: str
    email: str
    team_name: str | None = None
    work_location: str | None = None
    
    class Config:
        from_attributes = True
