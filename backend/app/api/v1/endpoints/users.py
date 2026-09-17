from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_current_user
from app.core.security import get_password_hash
from app.db.session import get_db
from app.db.models import User, Team
from app.schemas.user import UserResponse, UserSelfUpdate, TeamResponse
from typing import List

router = APIRouter()

@router.get("/events/{event_id}/teams", response_model=List[TeamResponse])
async def list_event_teams(
        event_id: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    teams = db.query(Team).filter(Team.event_id == event_id).order_by(Team.name.asc()).all()
    return [
        TeamResponse(
            id=team.id,
            event_id=team.event_id,
            team_name=team.name,
            member_count=0,
            created_at=team.created_at,
        )
        for team in teams
    ]



@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Lấy thông tin người dùng hiện tại.
    Endpoint này được RAG agent sử dụng để lấy context đầy đủ.
    """
    user = db.query(User).filter(User.id == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    # Xử lý roles
    roles = user.roles.split(",") if user.roles else ["USER"]
    if user.is_representative and "TEAM_REPRESENTATIVE" not in roles:
        roles.append("TEAM_REPRESENTATIVE")

    return UserResponse(
        id=user.id,
        emp_code=user.emp_code,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        work_location=user.work_location,
        team_id=user.team_id,
        team_name=user.team.name if user.team else None,
        is_representative=user.is_representative,
        roles=roles,
        created_at=user.created_at
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user_info(
        data: UserSelfUpdate,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Update only the authenticated user's phone and/or password."""
    user = db.query(User).filter(User.id == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    if data.phone is not None:
        user.phone = data.phone.strip() or None
    if data.password is not None:
        user.hashed_password = get_password_hash(data.password)

    db.commit()
    db.refresh(user)

    roles = user.roles.split(",") if user.roles else ["USER"]
    if user.is_representative and "TEAM_REPRESENTATIVE" not in roles:
        roles.append("TEAM_REPRESENTATIVE")

    return UserResponse(
        id=user.id,
        emp_code=user.emp_code,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        work_location=user.work_location,
        team_id=user.team_id,
        team_name=user.team.name if user.team else None,
        is_representative=user.is_representative,
        roles=roles,
        created_at=user.created_at,
    )
