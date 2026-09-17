from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_admin_role
from app.db.session import get_db
from app.schemas.admin import (
    EventStatistics,
    TeamStatistics,
    UserListItem,
)
from app.services import dashboard_svc

router = APIRouter()


@router.get(
    "/statistics/{event_id}",
    response_model=EventStatistics,
)
def get_event_statistics(
        event_id: str,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db),
):
    """
    [ADMIN ONLY] Lấy thống kê tổng quan của Event.

    Bao gồm:
    - Tổng số CBNV
    - Số đã/chưa đăng ký
    - Đăng ký theo Ca 1/Ca 2
    - Nhu cầu xe theo từng chặng
    - Slot chuyến bay
    - Phân bổ xe/phòng
    """

    return dashboard_svc.get_event_statistics(
        db=db,
        event_id=event_id,
    )


@router.get(
    "/teams/{event_id}",
    response_model=List[TeamStatistics],
)
def get_team_statistics(
        event_id: str,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db),
):
    """
    [ADMIN ONLY] Thống kê theo Team.
    """

    return dashboard_svc.get_team_statistics(
        db=db,
        event_id=event_id,
    )


@router.get(
    "/users/{event_id}",
    response_model=List[UserListItem],
)
def get_user_list(
        event_id: str,
        team_id: Optional[str] = Query(None),
        work_location: Optional[str] = Query(None),
        has_registered: Optional[bool] = Query(None),
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db),
):
    """
    [ADMIN ONLY] Danh sách CBNV với filter.

    Params:
        team_id: Lọc theo Team
        work_location: Lọc theo địa điểm (HN, HCM)
        has_registered: Lọc đã/chưa đăng ký
    """

    return dashboard_svc.get_user_list(
        db=db,
        event_id=event_id,
        team_id=team_id,
        work_location=work_location,
        has_registered=has_registered,
    )
