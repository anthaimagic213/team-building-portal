from app.services import email_svc

result = email_svc.send_email(
    to_email="2k6anthai@gmail.com",  # Gửi cho chính bạn để test
    subject="Test Email từ Team Building Portal",
    html_content="""
    <html>
        <body>
            <h2>Email Test</h2>
            <p>Nếu bạn nhận được email này, cấu hình SMTP đã thành công!</p>
        </body>
    </html>
    """,
)

if result:
    print("✅ Email đã được gửi thành công!")
else:
    print("❌ Gửi email thất bại. Kiểm tra lại cấu hình SMTP.")
