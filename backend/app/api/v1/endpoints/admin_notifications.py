from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.deps import require_admin_role, get_current_user
from app.db.session import get_db
from app.schemas.notification import (
    NotificationCreate,
    NotificationListResponse,
    NotificationResponse,
)
from app.services import notification_svc, audit_svc

router = APIRouter()


@router.post(
    "/",
    response_model=NotificationResponse,
)
def create_notification(
        data: NotificationCreate,
        request: Request,
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db),
):
    """
    [ADMIN ONLY] Tạo thông báo mới.

    Nếu send_email = True, hệ thống sẽ gửi email cho người nhận.
    """

    user_id = current_user.get("sub")

    notification = notification_svc.create_notification(
        db=db,
        data=data,
        created_by_user_id=user_id,
    )

    # Audit log
    audit_svc.log_action(
        db=db,
        user_id=user_id,
        emp_code=current_user.get("emp_code"),
        action="CREATE",
        entity_type="NOTIFICATION",
        entity_id=notification.id,
        new_data={
            "title": data.title,
            "type": data.notification_type,
            "target_user": data.target_user_id,
            "target_team": data.target_team_id,
            "send_email": data.send_email,
        },
        reason="BTC tạo thông báo mới",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    from app.db.models.user import User

    creator = db.query(User).filter(User.id == user_id).first()

    return NotificationResponse(
        id=notification.id,
        event_id=notification.event_id,
        target_user_id=notification.target_user_id,
        target_team_id=notification.target_team_id,
        title=notification.title,
        content=notification.content,
        notification_type=notification.notification_type,
        created_by=notification.created_by,
        created_by_name=creator.full_name if creator else None,
        created_at=notification.created_at,
        total_recipients=0,
        total_read=0,
    )


@router.get(
    "/{event_id}",
    response_model=NotificationListResponse,
)
def get_notifications(
        event_id: str,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        current_user: dict = Depends(require_admin_role),
        db: Session = Depends(get_db),
):
    """
    [ADMIN ONLY] Lấy danh sách thông báo.
    """

    notifications, total = notification_svc.get_notifications(
        db=db,
        event_id=event_id,
        page=page,
        page_size=page_size,
    )

    return NotificationListResponse(
        notifications=notifications,
        total=total,
        page=page,
        page_size=page_size,
    )
