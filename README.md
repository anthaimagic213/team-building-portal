# Team Building Portal

Portal quản lý các Event Team Building: đăng ký CBNV, Team, chuyến bay, xe đưa đón, khách sạn, Gala Dinner, thông báo và dashboard quản trị.

## Chạy nhanh bằng Docker

Yêu cầu:

- Docker Desktop hoặc Docker Engine có Docker Compose.
- Git.

```bash
git clone https://github.com/anthaimagic213/team-building-portal.git
cd team-building-portal
cp .env.example .env
docker compose up --build -d
```

Mở ứng dụng:

- Frontend: http://localhost
- Backend health: http://localhost:8000/health
- API docs: http://localhost:8000/api/docs

Dừng ứng dụng:

```bash
docker compose down
```

Xem log:

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

## Tài khoản kiểm thử

### Tài khoản Admin

Backend tự tạo tài khoản Admin khi khởi tạo database:

```text
Email:    admin@company.com
Password: Admin@123456
Role:     ADMIN, USER
```

### Tài khoản CBNV mẫu

Sau khi chạy full seed, tất cả CBNV mẫu đều dùng chung mật khẩu:

```text
Password: Test@123456
```

Ví dụ tài khoản CBNV có thể đăng nhập:

```text
Email:    e01t0101@company.com
Mã NV:    E01T0101
Password: Test@123456
Team:     E01 - Engineering
```

Một số tài khoản mẫu khác:

```text
e01t0102@company.com  / Test@123456
e01t0201@company.com  / Test@123456
e02t0101@company.com  / Test@123456
```

Các tài khoản CBNV được tạo theo mã `E<event>T<team><member>`. Full seed tạo
4 Event, 32 Team và 320 CBNV. Đây chỉ là thông tin đăng nhập cho môi trường
development/testing; không sử dụng các mật khẩu này trong production.

### Seed dữ liệu kiểm thử

Chạy từ terminal trong thư mục `backend`:

```bash
# Tạo admin, event, team và CBNV mẫu
python seed_dev.py --full

# Tạo thêm chuyến bay và xe mẫu cho các event
python seed_resources.py
```

Nếu chạy bằng WSL/Linux, có thể dùng `python3` thay cho `python`. Các script
seed có tính idempotent, có thể chạy lại mà không tạo bản ghi trùng.

Hãy đổi mật khẩu và `SECRET_KEY` trước khi dùng production.

## Cấu hình SMTP

Email là tùy chọn. Để bật email, sửa file `.env`:

```env
SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-account@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM_EMAIL=your-account@gmail.com
SMTP_TLS=true
```

Không dùng mật khẩu Gmail thông thường; dùng App Password. Không commit `.env`.

Hệ thống có thể gửi email khi:

- Admin tạo tài khoản.
- User đăng ký Event thành công.
- Admin tạo notification và chọn gửi email.

Nếu SMTP tắt, backend chỉ ghi log email dự kiến và các thao tác chính vẫn hoạt động.

## Luồng sử dụng chính

1. Admin tạo Event.
2. Admin tạo Team thuộc Event.
3. Admin tạo hoặc import Flight/Vehicle/Hotel thuộc Event.
4. User đăng ký Event và chọn Team.
5. Admin phân bổ chuyến bay theo `OUTBOUND` hoặc `RETURN`.
6. Admin phân bổ xe theo `ROUTE_1` đến `ROUTE_4`.
7. Admin import phòng khách sạn.
8. User xem mã chuyến, giờ khởi hành, xe, phòng và Gala seat tại `/journey`.

Mọi resource và allocation đều phải gắn với Event được chọn; dữ liệu các Event không bị trộn.

## Import phòng khách sạn

Tại `/admin/hotels`, chọn Event rồi kéo-thả file Excel.

Các cột bắt buộc/tùy chọn:

```text
hotel_name | room_code | room_type | emp_code_1 | emp_code_2 | emp_code_3 ... emp_code_9
```

Ví dụ:

```text
Vinpearl Đà Nẵng | A101 | Triple | HR_001 | BA_001 | BA_002
Vinpearl Đà Nẵng | A102 | Single | IT_001 |         |
```

Mỗi dòng là một phòng. Nếu nhiều người ở cùng phòng, đặt các `emp_code` trên cùng một dòng. Không tạo hai dòng trùng `room_code` trong cùng khách sạn.

## Import chuyến bay

Tại `/admin/flights`, chọn Event rồi kéo-thả file Excel.

```text
flight_code | direction | departure_time | arrival_time | origin | destination | total_slots
```

`direction` nhận `OUTBOUND` hoặc `RETURN`.

## Phát triển local không dùng Docker

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend terminal khác:

```bash
cd frontend
npm install
npm run dev
```

Khi chạy frontend Vite local, tạo `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

## Database

Schema chi tiết nằm trong:

```text
database.MD
```

Database mặc định là SQLite. Docker lưu database qua thư mục bind mount `backend/data` để dữ liệu không mất khi recreate container.

## Troubleshooting

Nếu port 80 đã được sử dụng:

```bash
docker compose down
```

Sau đó đổi mapping trong `docker-compose.yml`, ví dụ:

```yaml
ports:
  - "8080:80"
```

và truy cập http://localhost:8080.

Nếu Event bị kẹt `ALLOCATION_IN_PROGRESS`, dùng nút **Xóa phân bổ cũ và chạy lại** ở trang allocation tương ứng.

## Bảo mật

- Không commit `.env`, database hoặc SMTP credentials.
- Đổi `SECRET_KEY`, mật khẩu Admin và SMTP App Password khi triển khai.
- File `.env` hiện tại nếu từng được chia sẻ/public cần rotate SMTP credentials ngay.