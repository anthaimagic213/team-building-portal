import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings


def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
) -> bool:
    """
    Gửi email.

    Args:
        to_email: Email người nhận
        subject: Tiêu đề
        html_content: Nội dung HTML
        text_content: Nội dung text (fallback)

    Returns:
        True nếu gửi thành công
    """

    if not settings.SMTP_ENABLED:
        print(f"[EMAIL] SMTP disabled. Would send to {to_email}: {subject}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        if text_content:
            part1 = MIMEText(text_content, "plain", "utf-8")
            msg.attach(part1)

        part2 = MIMEText(html_content, "html", "utf-8")
        msg.attach(part2)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()

            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

            server.send_message(msg)

        print(f"✅ Email sent to {to_email}: {subject}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {str(e)}")
        return False


def send_registration_confirmation(
        to_email: str,
        user_name: str,
        event_name: str,
        event_date: str,
) -> bool:
    """
    Gửi email xác nhận đăng ký.
    """

    subject = f"Xác nhận đăng ký {event_name}"

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Xin chào {user_name},</h2>
            <p>Bạn đã đăng ký thành công cho chương trình <strong>{event_name}</strong>.</p>
            <p><strong>Thời gian:</strong> {event_date}</p>
            <p>Vui lòng đăng nhập vào hệ thống để xem chi tiết hành trình của bạn:</p>
            <p><a href="{settings.FRONTEND_URL}/journey">Xem hành trình của tôi</a></p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Email này được gửi tự động. Vui lòng không trả lời.
            </p>
        </body>
    </html>
    """

    text_content = f"""
    Xin chào {user_name},

    Bạn đã đăng ký thành công cho chương trình {event_name}.

    Thời gian: {event_date}

    Vui lòng đăng nhập vào hệ thống để xem chi tiết.
    """

    return send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )


def send_information_published(
        to_email: str,
        user_name: str,
        event_name: str,
) -> bool:
    """
    Gửi email thông báo BTC đã công bố thông tin.
    """

    subject = f"Thông tin hành trình {event_name} đã được công bố"

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Xin chào {user_name},</h2>
            <p>Ban Tổ Chức đã hoàn tất phân bổ và công bố thông tin hành trình cho chương trình <strong>{event_name}</strong>.</p>
            <p>Vui lòng đăng nhập vào hệ thống để xem:</p>
            <ul>
                <li>Chuyến bay</li>
                <li>Xe đưa đón</li>
                <li>Khách sạn</li>
                <li>Gala Dinner</li>
                <li>Lịch trình chi tiết</li>
            </ul>
            <p><a href="{settings.FRONTEND_URL}/journey" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Xem hành trình</a></p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Email này được gửi tự động. Vui lòng không trả lời.
            </p>
        </body>
    </html>
    """

    return send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
    )


def send_notification_email(
        to_email: str,
        user_name: str,
        title: str,
        content: str,
        notification_type: str = "INFO",
) -> bool:
    """
    Gửi email thông báo từ BTC.
    """

    type_colors = {
        "INFO": "#007bff",
        "WARNING": "#ffc107",
        "URGENT": "#dc3545",
    }

    color = type_colors.get(notification_type, "#007bff")

    subject = f"[{notification_type}] {title}"

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Xin chào {user_name},</h2>
            <div style="border-left: 4px solid {color}; padding-left: 15px; margin: 20px 0;">
                <h3 style="color: {color};">{title}</h3>
                <p>{content}</p>
            </div>
            <p><a href="{settings.FRONTEND_URL}/journey">Xem hành trình của tôi</a></p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Email này được gửi tự động. Vui lòng không trả lời.
            </p>
        </body>
    </html>
    """

    return send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
    )


def send_email_verification(
        to_email: str,
        user_name: str,
        verification_token: str,
) -> bool:
    """
    Gửi email xác thực tài khoản.
    """

    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"

    subject = "Xác thực email đăng ký hệ thống Team Building"

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Xin chào {user_name},</h2>
            <p>Cảm ơn bạn đã đăng ký tài khoản.</p>
            <p>Vui lòng click vào link bên dưới để xác thực email:</p>
            <p><a href="{verification_url}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Xác thực email</a></p>
            <p>Hoặc copy link sau vào trình duyệt:</p>
            <p style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; word-break: break-all;">
                {verification_url}
            </p>
            <p style="color: #dc3545; font-weight: bold;">Link xác thực sẽ hết hạn sau 24 giờ.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email.
            </p>
        </body>
    </html>
    """

    return send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
    )
