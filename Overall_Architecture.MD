# BẢN THIẾT KẾ KIẾN TRÚC TỔNG THỂ (OVERALL ARCHITECTURE)
**Dự án:** Hệ thống Quản lý Team Building (One-stop Portal)
**Giai đoạn:** Phase 1 (MVP) & Thiết kế nền tảng cho Phase 2 (Agentic RAG)[cite: 2, 3]

## 1. Tổng quan Kiến trúc
Hệ thống được thiết kế theo kiến trúc Monolith tinh gọn, tuân thủ nguyên tắc Single Source of Truth (SSOT)[cite: 2, 3]. Hệ thống sử dụng FastAPI cho Backend, React cho Frontend, và SQLite làm cơ sở dữ liệu chính[cite: 3]. Để chuẩn bị cho tính năng Chatbot RAG ở Phase 2, cơ sở dữ liệu được thiết kế theo hướng Semantic (ngữ nghĩa rõ ràng) và Backend cung cấp sẵn các tool calling API bóc tách dữ liệu cá nhân hóa dựa trên JWT token[cite: 3].

## 2. Phân chia Module & Yêu cầu Nghiệp vụ
Hệ thống bao gồm 05 module cốt lõi dành cho người dùng và 1 khu vực quản trị:
*   **Module 1 – Đăng ký Team Building:** CBNV xác nhận tham gia, đồng ý quy định, đăng ký nguyện vọng (Ca 1/Ca 2) và nhu cầu xe đưa đón[cite: 2]. Chức năng chỉnh sửa bị khóa khi trạng thái chuyển sang Registration Closed[cite: 3]. Trường hợp hủy xe sát giờ sẽ hiển thị cảnh báo không thể hoàn tác và không chạy lại Auto Allocation[cite: 3].
*   **Module 2 – Quản lý & phân bổ chuyến bay/khách sạn:** 
    *   *Chuyến bay:* Thuật toán Auto Flight Allocation ưu tiên Team đi cùng nhau cao hơn nguyện vọng cá nhân; Team lẻ sẽ bị đẩy cả nhóm sang chuyến khác thay vì tách người để đảm bảo cảm xúc nhân viên[cite: 2, 3]. Cho phép BTC kéo thả thủ công (Manual Adjustment) cho các trường hợp ngoại lệ[cite: 2].
    *   *Khách sạn:* Trong Phase 1 MVP, hệ thống không tự động phân bổ phòng mà BTC sẽ xuất danh sách, Team Leader tự chia, sau đó BTC Import Excel lại vào hệ thống[cite: 2, 3].
*   **Module 3 – Quản lý & điều phối xe:** Quản lý 04 chặng di chuyển[cite: 2]. Phân bổ xe tự động ưu tiên người cùng chuyến bay và cùng Team[cite: 2].
*   **Module 4 – Gala Dinner:** Trải nghiệm như mua vé rạp phim với cơ chế bốc thăm thứ tự (Random turn) và Team Leader (hoặc người được ủy quyền) chọn ghế[cite: 2, 3]. Không sử dụng WebSocket, thay vào đó kết hợp HTTP Polling trên React và Optimistic Locking trên SQLite để xử lý truy cập đồng thời (Concurrency)[cite: 3].
*   **Module 5 – My Team Building Journey:** Dashboard cá nhân xem toàn bộ hành trình tập trung (chuyến bay, xe, phòng, ghế Gala, lịch trình)[cite: 2].
*   **Admin Dashboard:** Khu vực quản trị tập trung Master Data, cấu hình nguồn lực (chuyến bay, xe), gửi notification (Email qua BackgroundTasks), và Audit Log[cite: 2, 3].

## 3. Thư viện & Tech Stack Đề xuất
*   **Backend:**
    *   Framework: `FastAPI`[cite: 3].
    *   Auth: `fastapi-users` hoặc `PyJWT` cho việc triển khai JWT và SSO nhanh gọn[cite: 3].
    *   Database ORM: `SQLAlchemy` kết nối với SQLite[cite: 3].
    *   Xử lý file: `pandas` để bóc tách và import file Excel/CSV[cite: 3].
    *   Background Jobs: Sử dụng `BackgroundTasks` tích hợp sẵn của FastAPI để gửi Email tự động mà không chặn luồng API[cite: 3].
*   **Frontend:**
    *   Thư viện lõi: `React` (sử dụng Vite)[cite: 3].
    *   Giao diện: `Tailwind CSS` để xây dựng Responsive UI cho Web/Mobile (đặc biệt là dạng Timeline cho My Journey)[cite: 3].
    *   Data Fetching: `React Query` để phục vụ cơ chế HTTP Polling (ví dụ: refetch mỗi 2-3 giây cho Module Gala Dinner)[cite: 3].
*   **DevOps & Deployment:** `Docker`, `Docker Compose`, và `Nginx` (làm proxy và phục vụ file tĩnh)[cite: 3].

## 4. Thiết kế JWT Payload (Tối ưu cho Tool Calling RAG)
Để Agentic RAG truy xuất dữ liệu cá nhân hóa siêu tốc mà không cần join bảng phức tạp, JWT Payload lưu trữ các thông tin định danh (Context) thiết yếu. Đồng thời, áp dụng Role-Based Access Control (RBAC) bằng mảng `roles` để xử lý sự giao thoa quyền (Ví dụ: BTC cũng là CBNV tham gia chuyến đi)[cite: 3].

{
  "sub": "uuid-user-1234",
  "emp_code": "NV001",
  "team_id": "uuid-team-ai",
  "active_event_id": "uuid-event-2026",
  "roles": ["USER", "ADMIN", "TEAM_REPRESENTATIVE"],
  "exp": 1698765432
}

*   `team_id` và `active_event_id`: Giúp Tool Calling của Agent bóc tách trực tiếp và truy vấn CSDL ngay lập tức cho các câu hỏi như "Ai bay cùng tôi?"[cite: 3].
*   `roles`: Xác định quyền gọi Tool liên quan đến thao tác dữ liệu (VD: quyền chọn ghế cho `TEAM_REPRESENTATIVE`)[cite: 3].

## 5. Thiết kế Cơ sở dữ liệu SQLite (Semantic Schema)
Các bảng được chuẩn hóa SSOT và đặt tên trường rõ nghĩa (tiếng Anh) để LLM có thể đọc và hiểu Schema khi cấu hình Agent Tool Calling[cite: 3].

*   **Table `events`**
    *   `id` (PK)
    *   `event_name`: Tên chương trình
    *   `status`: Trạng thái sự kiện (OPEN_REG, CLOSED_REG, ALLOCATING, PUBLISHED)[cite: 3]
*   **Table `teams`**
    *   `id` (PK)
    *   `event_id` (FK)
    *   `team_name`
*   **Table `users`**
    *   `id` (PK)
    *   `emp_code`: Mã nhân viên (Unique)[cite: 3]
    *   `full_name`, `email`
    *   `team_id` (FK)
    *   `is_representative`: Boolean (Phục vụ ủy quyền bốc thăm Gala Dinner nếu Team Leader vắng mặt)[cite: 3]
*   **Table `flights`**
    *   `id` (PK), `event_id` (FK)
    *   `flight_code`, `total_slots`[cite: 3]
    *   `departure_time`, `arrival_time`: Định dạng ISO8601 (Semantic giúp RAG dễ hiểu thời gian)[cite: 3]
    *   `origin`, `destination`[cite: 3]
*   **Table `vehicles`**
    *   `id` (PK), `event_id` (FK)
    *   `vehicle_name`, `capacity`[cite: 3]
    *   `route_type`: Enum (HN_AIRPORT, AIRPORT_HOTEL...)[cite: 3]
    *   `departure_time`, `pickup_location`[cite: 3]
*   **Table `registrations` (Bảng trung tâm SSOT)**
    *   `id` (PK), `user_id` (FK), `event_id` (FK)[cite: 3]
    *   `is_participating`: Boolean[cite: 3]
    *   `desired_shift`: Enum (SHIFT_1, SHIFT_2)[cite: 3]
    *   `assigned_flight_id`, `assigned_vehicle_route_1_id`, vân vân: FK (Nullable)[cite: 3]
*   **Table `gala_seats` (Phục vụ Optimistic Locking)**
    *   `id` (PK), `event_id` (FK)
    *   `seat_code` (VD: A1, A2)[cite: 3]
    *   `status`: Enum (AVAILABLE, LOCKING, CONFIRMED)[cite: 3]
    *   `locked_by_team_id`: FK (Nullable)[cite: 3]
    *   `locked_at`: Timestamp (Nullable)[cite: 3]

## 6. Thiết kế API Endpoints (Giai đoạn MVP - Đầy đủ)
Dưới đây là danh sách toàn bộ API cần thiết để đáp ứng yêu cầu nghiệp vụ, quản trị, điều phối và chuẩn bị cho mô hình RAG tích hợp Tool Calling[cite: 2, 3].

**Auth & Users (Xác thực & Người dùng):**
*   `POST /api/v1/auth/login`: Xác thực tài khoản công ty/SSO và trả về JWT token[cite: 2, 3].
*   `GET /api/v1/users/me`: Trả về thông tin Master Data của user hiện tại[cite: 2].

**Cấu hình Sự kiện & Master Data (Yêu cầu role ADMIN):**
*   `GET /api/v1/events/active`: Trả về thông tin và trạng thái (Registration Open/Closed, Information Published) của sự kiện hiện tại để Frontend quyết định hiển thị màn hình nào[cite: 2].
*   `POST/PUT/DELETE /api/v1/admin/events`: Thêm/sửa/xóa thông tin các kỳ Team Building[cite: 2].
*   `PUT /api/v1/admin/events/{id}/status`: Cập nhật trạng thái vòng đời chương trình[cite: 2].
*   `GET/POST/PUT/DELETE /api/v1/admin/teams`: Quản lý Master Data danh sách Team/Bộ phận[cite: 2].
*   `GET/POST/PUT/DELETE /api/v1/admin/flights`: Quản lý thông tin chuyến bay, thời gian và số lượng slot[cite: 2].
*   `GET/POST/PUT/DELETE /api/v1/admin/vehicles`: Quản lý các chặng xe, sức chứa, địa điểm đón/trả và Trưởng xe[cite: 2].

**Registration (Đăng ký Team Building):**
*   `GET /api/v1/registrations/me`: Trả về form đăng ký hiện tại của user để xem lại hoặc cập nhật thông tin cá nhân trong thời gian cho phép[cite: 2].
*   `POST /api/v1/registrations/submit`: Ghi nhận xác nhận tham gia, nguyện vọng ca đi, nhu cầu xe[cite: 2]. API này sẽ trigger BackgroundTasks để gửi email thông báo thành công[cite: 2, 3].
*   `PUT /api/v1/registrations/cancel-vehicle`: Cho phép chuyển nhu cầu xe từ Có sang Không, cập nhật slot trống cho BTC xử lý nhưng tuyệt đối không chạy lại Auto Allocation[cite: 3].

**Điều phối (Allocation - Yêu cầu role ADMIN):**
*   `POST /api/v1/admin/allocations/flights/auto`: Chạy thuật toán phân bổ chuyến bay ưu tiên giữ Team đi cùng nhau, đẩy các ngoại lệ (flag) vào danh sách chưa phân bổ[cite: 2, 3].
*   `PUT /api/v1/admin/allocations/flights/manual`: Điều chỉnh chuyến bay thủ công cho cá nhân hoặc toàn bộ Team[cite: 2].
*   `POST /api/v1/admin/allocations/vehicles/auto`: Chạy thuật toán phân xe ưu tiên người cùng chuyến bay và cùng Team[cite: 2].
*   `PUT /api/v1/admin/allocations/vehicles/manual`: Điều chỉnh danh sách xe thủ công và cập nhật người làm Trưởng xe[cite: 2].
*   `POST /api/v1/admin/import/hotels`: Upload và bóc tách file Excel phân phòng, sau đó import dữ liệu vào hệ thống thay cho thuật toán tự động[cite: 2, 3].

**Admin Dashboard & Báo cáo (Yêu cầu role ADMIN):**
*   `GET /api/v1/admin/dashboard/stats`: Lấy chỉ số tổng quan gồm tổng số CBNV, tỷ lệ đăng ký các ca, nhu cầu xe, và tình trạng lấp đầy slot chuyến bay/xe[cite: 2].
*   `GET /api/v1/admin/export/registrations`: Trích xuất toàn bộ dữ liệu đăng ký và kết quả phân bổ ra định dạng Excel hoặc CSV[cite: 2].

**Gala Dinner (Concurrency & Seat Selection):**
*   `GET /api/v1/gala/seats`: Trả về sơ đồ trạng thái ghế, Frontend gọi HTTP Polling định kỳ mỗi 2-3 giây để cập nhật[cite: 2, 3].
*   `POST /api/v1/gala/seats/lock`: Đại diện Team thao tác chọn ghế[cite: 2]. API kiểm tra `status = 'AVAILABLE'`, cập nhật thành `LOCKING` và `locked_at = NOW()` dựa trên Optimistic Locking. Nếu `rowcount == 0` sẽ ném lỗi 409 Conflict[cite: 3].
*   `POST /api/v1/gala/seats/confirm`: Xác nhận chuyển ghế sang trạng thái `Confirmed` trong thời gian khóa tạm thời[cite: 2, 3].

**My Journey & Agentic RAG Context (Hành trình cá nhân):**
*   `GET /api/v1/journey/me`: Trả về toàn bộ thông tin chuyến bay, xe, phòng và ghế Gala trên một màn hình tập trung[cite: 2]. Data Model của endpoint này sử dụng Pydantic Field Descriptions rõ ràng để Agent RAG dễ dàng nhận diện dưới dạng Tool Calling, sử dụng JWT Token để lấy chính xác thông tin hành trình[cite: 3].
## 7. Cấu trúc thư mục & Triển khai Docker (Chi tiết Backend)
Hệ thống sử dụng mô hình Monorepo và bắt buộc dùng Docker Volume cho SQLite để tránh mất dữ liệu khi container sập[cite: 3]. Dưới đây là cấu trúc chi tiết đến từng file của module Backend (FastAPI), phân tách rõ ràng các layer: API (Routing), Services (Business Logic), DB (Database Models), và Schemas (Data Validation). 

Phần Frontend tạm thời được thu gọn để tập trung vào logic hệ thống.

```text
/team-building-portal
├── .env.example               # Khai báo SMTP, Secret Key, Database URL (Không commit .env thật)[cite: 3]
├── docker-compose.yml         # Chứa cấu hình service backend, frontend và map Volume cho SQLite[cite: 3]
│
├── backend/
│   ├── Dockerfile             # Chạy FastAPI bằng Uvicorn[cite: 3]
│   ├── requirements.txt       # Chứa danh sách thư viện (fastapi, sqlalchemy, pydantic, pandas...)
│   ├── data/                  # Nơi chứa file teambuilding.db (Được mount ra Host)[cite: 3]
│   │   └── .gitkeep           # Đảm bảo Git giữ lại thư mục rỗng này
│   │
│   └── app/                   # Root module của ứng dụng FastAPI
│       ├── __init__.py
│       ├── main.py            # Entry point: Khởi tạo app, cấu hình CORS, include routers[cite: 3]
│       │
│       ├── core/              # Config, Security, JWT logic[cite: 3]
│       │   ├── config.py      # Load biến môi trường từ .env (Pydantic BaseSettings)
│       │   ├── security.py    # Logic hash mật khẩu, tạo và verify JWT token
│       │   ├── exceptions.py  # Custom HTTP Exceptions (400, 404, 409 Conflict cho Gala...)
│       │   └── deps.py        # Dependency Injection (get_db, get_current_user, require_admin_role)
│       │
│       ├── db/                # SQLAlchemy Models (Thiết kế Semantic Database)[cite: 3]
│       │   ├── session.py     # Khởi tạo engine và session SQLite (mode read-write và read-only)
│       │   ├── base.py        # Base class cho SQLAlchemy Declarative
│       │   └── models/        # Phân tách models theo từng Domain
│       │       ├── __init__.py
│       │       ├── event.py   # Table: events
│       │       ├── user.py    # Table: users, teams
│       │       ├── resource.py# Table: flights, vehicles
│       │       ├── register.py# Table: registrations (Single Source of Truth)
│       │       └── gala.py    # Table: gala_seats
│       │
│       ├── schemas/           # Pydantic models (Data validation & API Schema)[cite: 3]
│       │   ├── __init__.py
│       │   ├── auth.py        # Token response, Login request schemas
│       │   ├── user.py        # User & Team schemas
│       │   ├── resource.py    # Flight, Vehicle schemas
│       │   ├── register.py    # Form submit schemas (Shift, Vehicle Needs)
│       │   └── journey.py     # Pydantic Field Descriptions cho RAG Tool Calling Phase 2[cite: 3]
│       │
│       ├── api/               # Chứa các router (v1/ và agent/ cho Phase 2)[cite: 3]
│       │   ├── __init__.py
│       │   ├── api_router.py  # Gộp tất cả router của v1 vào chung một biến APIRouter
│       │   ├── v1/
│       │   │   └── endpoints/
│       │   │       ├── auth.py          # POST /login
│       │   │       ├── users.py         # GET /users/me
│       │   │       ├── admin_core.py    # Quản lý Events, Teams, Trạng thái chương trình
│       │   │       ├── admin_res.py     # Quản lý Flights, Vehicles, Import Hotels
│       │   │       ├── registrations.py # Đăng ký, Hủy xe (Cancel-vehicle)
│       │   │       ├── allocations.py   # Chạy Auto Allocation & Manual Adjustment (Chuyến bay, Xe)
│       │   │       ├── gala.py          # GET (Polling), POST lock, POST confirm ghế Gala
│       │   │       ├── dashboard.py     # Thống kê Dashboard & Export Excel/CSV
│       │   │       └── journey.py       # Lấy My Journey (Trả về Context cho Agent/User)
│       │   │
│       │   └── agent/         # Thư mục chờ sẵn cho Phase 2[cite: 3]
│       │       └── tools.py   # Expose các API Read-only (SELECT) dành riêng cho Agent RAG gọi
│       │
│       ├── services/          # Business logic, Auto Allocation, Email Tasks[cite: 3]
│       │   ├── __init__.py
│       │   ├── email_svc.py       # Logic gửi email đăng ký/thay đổi đẩy vào BackgroundTasks
│       │   ├── alloc_flight_svc.py# Thuật toán CSP (Constraint) xếp chuyến bay theo Team
│       │   ├── alloc_vehicle_svc.py# Logic xếp xe ưu tiên cùng chuyến bay/cùng Team
│       │   ├── gala_svc.py        # Logic Optimistic Locking, xử lý rowcount == 0 (Conflict)
│       │   └── export_svc.py      # Query tổng hợp SSOT ra dạng phẳng để xuất file
│       │
│       └── utils/             # Các hàm tiện ích hỗ trợ (Helpers)
│           ├── __init__.py
│           ├── excel_parser.py # Dùng thư viện pandas đọc file import phòng khách sạn/user
│           └── string_utils.py # Hàm chuẩn hóa chuỗi, tạo mã code ngẫu nhiên
│
└── frontend/
    ├── Dockerfile             # Multi-stage build: Node.js build -> Nginx serve[cite: 3]
    ├── nginx.conf             # Proxy pass đường dẫn /api/ sang Backend, tránh CORS[cite: 3]
    └── src/                   # React components, pages, api services (Chi tiết phát triển ở Frontend)[cite: 3]