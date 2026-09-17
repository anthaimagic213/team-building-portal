from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException, BadRequestException
from app.db.models.event import Event
from app.db.models.notification import Notification, UserNotificationRead
from app.db.models.register import Registration
from app.db.models.user import User, Team
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
)
from app.services import email_svc


def create_notification(
        db: Session,
        data: NotificationCreate,
        created_by_user_id: str,
) -> Notification:
    """
    Tạo thông báo mới.

    Nếu send_email = True, gửi email cho tất cả người nhận.
    """

    # Validate event
    event = db.query(Event).filter(Event.id == data.event_id).first()
    if not event:
        raise NotFoundException(detail="Không tìm thấy Event")

    # Validate target user (nếu có)
    if data.target_user_id:
        user = db.query(User).filter(User.id == data.target_user_id).first()
        if not user:
            raise NotFoundException(detail="Không tìm thấy user")

    # Validate target team (nếu có)
    if data.target_team_id:
        team = db.query(Team).filter(Team.id == data.target_team_id).first()
        if not team:
            raise NotFoundException(detail="Không tìm thấy Team")

    # Tạo notification
    notification = Notification(
        event_id=data.event_id,
        target_user_id=data.target_user_id,
        target_team_id=data.target_team_id,
        title=data.title,
        content=data.content,
        notification_type=data.notification_type,
        created_by=created_by_user_id,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    # Gửi email nếu cần
    if data.send_email:
        recipients = _get_notification_recipients(
            db=db,
            event_id=data.event_id,
            target_user_id=data.target_user_id,
            target_team_id=data.target_team_id,
        )

        for user in recipients:
            email_svc.send_notification_email(
                to_email=user.email,
                user_name=user.full_name,
                title=data.title,
                content=data.content,
                notification_type=data.notification_type,
            )

    return notification


def get_notifications(
        db: Session,
        event_id: str,
        page: int = 1,
        page_size: int = 20,
) -> tuple[List[NotificationResponse], int]:
    """
    Lấy danh sách thông báo của Event.
    """

    query = (
        db.query(Notification)
        .filter(Notification.event_id == event_id)
        .order_by(Notification.created_at.desc())
    )

    total = query.count()

    notifications = (
        query
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []

    for notif in notifications:
        creator = (
            db.query(User)
            .filter(User.id == notif.created_by)
            .first()
        )

        total_recipients = _count_notification_recipients(
            db=db,
            event_id=notif.event_id,
            target_user_id=notif.target_user_id,
            target_team_id=notif.target_team_id,
        )

        total_read = (
            db.query(UserNotificationRead)
            .filter(UserNotificationRead.notification_id == notif.id)
            .count()
        )

        result.append(
            NotificationResponse(
                id=notif.id,
                event_id=notif.event_id,
                target_user_id=notif.target_user_id,
                target_team_id=notif.target_team_id,
                title=notif.title,
                content=notif.content,
                notification_type=notif.notification_type,
                created_by=notif.created_by,
                created_by_name=creator.full_name if creator else None,
                created_at=notif.created_at,
                total_recipients=total_recipients,
                total_read=total_read,
            )
        )

    return result, total


def _get_notification_recipients(
        db: Session,
        event_id: str,
        target_user_id: Optional[str],
        target_team_id: Optional[str],
) -> List[User]:
    """
    Lấy danh sách người nhận thông báo.
    """

    if target_user_id:
        # Gửi cho 1 user cụ thể
        user = db.query(User).filter(User.id == target_user_id).first()
        return [user] if user else []

    elif target_team_id:
        # Gửi cho toàn bộ Team
        users = db.query(User).filter(User.team_id == target_team_id).all()
        return users

    else:
        # Gửi cho toàn bộ người đã đăng ký Event
        registrations = (
            db.query(Registration)
            .filter(
                Registration.event_id == event_id,
                Registration.is_participating.is_(True),
            )
            .all()
        )

        user_ids = [r.user_id for r in registrations]

        users = (
            db.query(User)
            .filter(User.id.in_(user_ids))
            .all()
        )

        return users


def _count_notification_recipients(
        db: Session,
        event_id: str,
        target_user_id: Optional[str],
        target_team_id: Optional[str],
) -> int:
    """
    Đếm số người nhận thông báo.
    """

    recipients = _get_notification_recipients(
        db=db,
        event_id=event_id,
        target_user_id=target_user_id,
        target_team_id=target_team_id,
    )

    return len(recipients)
