from sqlalchemy.orm import Session
from app.db.models import Registration, User
from app.core.config import settings
from app.db.models.event import Event
from app.services import email_svc


def send_registration_confirmation_email(db: Session, registration_id: str):
    """
    Gửi email xác nhận đăng ký thành công.

    Được gọi qua BackgroundTasks để không block API response.

    TODO: Tích hợp SMTP server thực tế khi deploy production.
    """
    registration = db.query(Registration).filter(Registration.id == registration_id).first()
    if not registration:
        return

    user = db.query(User).filter(User.id == registration.user_id).first()
    if not user:
        return

    event = db.query(Event).filter(Event.id == registration.event_id).first()
    if event:
        email_svc.send_registration_confirmation(
            to_email=user.email,
            user_name=user.full_name,
            event_name=event.name,
            event_date=f"{event.start_date} - {event.end_date}",
        )


def send_account_created_email(user_id: str, password: str):
    """Send credentials after an admin-created account is committed."""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        email_svc.send_email(
            to_email=user.email,
            subject="Tài khoản Team Building đã được tạo",
            html_content=(
                f"<p>Xin chào {user.full_name},</p>"
                f"<p>Tài khoản của bạn đã được tạo thành công.</p>"
                f"<p><b>Mã nhân viên:</b> {user.emp_code}<br/>"
                f"<b>Email:</b> {user.email}<br/>"
                f"<b>Mật khẩu:</b> {password}</p>"
                f"<p><a href='{settings.FRONTEND_URL}/login'>Đăng nhập hệ thống</a></p>"
            ),
            text_content=f"Tài khoản đã tạo. Mã NV: {user.emp_code}; Mật khẩu: {password}",
        )
    finally:
        db.close()
