from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base, generate_uuid


class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    event = relationship("Event", back_populates="teams")
    users = relationship("User", back_populates="team")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    emp_code = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    phone = Column(String, nullable=True)
    work_location = Column(String, nullable=True)

    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    roles = Column(String, default="USER")

    is_representative = Column(Boolean, default=False)
    is_priority = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    team = relationship("Team", back_populates="users")
    registrations = relationship("Registration", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    """
    Refresh Token Model

    Lưu refresh tokens trong database để:
    - Có thể revoke (thu hồi) token
    - Track login sessions
    - Security audit
    """
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Token string (hashed)
    token = Column(String, nullable=False, unique=True, index=True)

    # Expiry
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Revocation
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Relationship
    user = relationship("User", back_populates="refresh_tokens")
