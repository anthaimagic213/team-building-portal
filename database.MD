# Database Schema

Schema hiện tại được định nghĩa bởi SQLAlchemy models trong `backend/app/db/models` và khởi tạo/nâng cấp tại `backend/app/db/session.py`.

Database hiện dùng `Base.metadata.create_all()` cùng một số câu lệnh `ALTER TABLE` tương thích dữ liệu cũ; chưa dùng migration versioned như Alembic.

## Tổng quan

```text
events
├── teams
├── registrations ── users
├── flights
├── vehicles
├── hotels ── hotel_rooms
├── event_schedules
├── notifications ── user_notification_reads
├── gala_configs
├── gala_seats
├── gala_team_turns
└── event_representatives
```

## `events`

| Cột | Kiểu | Null | Ghi chú |
|---|---|---:|---|
| `id` | VARCHAR | Không | PK, UUID, index |
| `name` | VARCHAR | Không | Tên Event |
| `status` | VARCHAR | Không | `DRAFT`, `REGISTRATION_OPEN`, `REGISTRATION_CLOSED`, `ALLOCATION_IN_PROGRESS`, `ALLOCATION_COMPLETED`, `EVENT_ACTIVE`, `EVENT_COMPLETED` |
| `start_date`, `end_date` | DATETIME | Có | Thời gian Event |
| `location` | VARCHAR | Có | Địa điểm |
| `registration_deadline` | DATETIME | Có | Hạn đăng ký |
| `description` | TEXT | Có | Mô tả |
| `created_at`, `updated_at` | DATETIME | Có | Audit thời gian |

## `users`

| Cột | Kiểu | Null | Ghi chú |
|---|---|---:|---|
| `id` | VARCHAR | Không | PK, UUID |
| `emp_code` | VARCHAR | Không | Unique, index |
| `full_name`, `email` | VARCHAR | Không | Email unique, index |
| `hashed_password` | VARCHAR | Không | Mật khẩu hash |
| `phone`, `work_location` | VARCHAR | Có | Thông tin nhân sự |
| `team_id` | VARCHAR | Có | FK → `teams.id`, field legacy/global |
| `roles` | VARCHAR | Có | Chuỗi role phân cách dấu phẩy |
| `is_representative` | BOOLEAN | Có | Legacy; quyền representative mới dùng bảng riêng |
| `is_priority` | BOOLEAN | Có | Ưu tiên |
| `created_at`, `updated_at` | DATETIME | Có | Audit thời gian |

## `teams`

| Cột | Kiểu | Null | Ghi chú |
|---|---|---:|---|
| `id` | VARCHAR | Không | PK, UUID |
| `event_id` | VARCHAR | Không | FK → `events.id` |
| `name` | VARCHAR | Không | Unique toàn DB hiện tại |
| `created_at` | DATETIME | Có | Thời gian tạo |

## `registrations`

Một user có thể có nhiều registration, mỗi Event một dòng.

| Cột | Kiểu | Null | Ghi chú |
|---|---|---:|---|
| `id` | VARCHAR | Không | PK, UUID |
| `user_id` | VARCHAR | Không | FK → `users.id` |
| `event_id` | VARCHAR | Không | FK → `events.id` |
| `team_id` | VARCHAR | Có | FK → `teams.id`, Team của user trong Event |
| `is_participating` | BOOLEAN | Có | Có tham gia |
| `desired_shift` | VARCHAR | Có | `SHIFT_1`/`SHIFT_2` |
| `need_vehicle_route_1..4` | BOOLEAN | Có | Nhu cầu xe từng route |
| `pickup_location_route_1`, `pickup_location_route_4` | VARCHAR | Có | Điểm đón |
| `wishes` | TEXT | Có | Nguyện vọng |
| `assigned_flight_id` | VARCHAR | Có | FK legacy → `flights.id` |
| `assigned_outbound_flight_id` | VARCHAR | Có | FK → `flights.id`, chuyến đi |
| `assigned_return_flight_id` | VARCHAR | Có | FK → `flights.id`, chuyến về |
| `assigned_vehicle_1_id..4_id` | VARCHAR | Có | FK → `vehicles.id` |
| `assigned_hotel_room` | VARCHAR | Có | `room_code` của phòng |
| `created_at`, `updated_at` | DATETIME | Có | Audit thời gian |

> Flight allocation phải dùng hai field theo chiều; không ghi đè qua `assigned_flight_id`.

## `flights`

| Cột | Kiểu | Null | Ghi chú |
|---|---|---:|---|
| `id` | VARCHAR | Không | PK, UUID |
| `event_id` | VARCHAR | Không | FK → `events.id` |
| `flight_code` | VARCHAR | Không | Mã chuyến |
| `direction` | VARCHAR | Không | `OUTBOUND` hoặc `RETURN` |
| `departure_time`, `arrival_time` | DATETIME | Không | Thời gian |
| `origin`, `destination` | VARCHAR | Không | Điểm đi/đến |
| `total_slots` | INTEGER | Có | Tổng slot |

## `vehicles`

| Cột | Kiểu | Null | Ghi chú |
|---|---|---:|---|
| `id` | VARCHAR | Không | PK, UUID |
| `event_id` | VARCHAR | Không | FK → `events.id` |
| `vehicle_name` | VARCHAR | Không | Tên xe |
| `route_type` | VARCHAR | Không | `ROUTE_1` đến `ROUTE_4` |
| `departure_time` | DATETIME | Không | Giờ chạy |
| `pickup_location` | VARCHAR | Không | Điểm đón |
| `dropoff_location` | VARCHAR | Có | Điểm trả |
| `capacity` | INTEGER | Có | Sức chứa |
| `captain_id` | VARCHAR | Có | FK → `users.id` |
| `notes` | TEXT | Có | Ghi chú |

## `hotels` và `hotel_rooms`

`hotels`: `id` PK; `event_id` FK; `hotel_name` bắt buộc và unique cùng Event; `address`, `phone` nullable; `total_rooms` bắt buộc.

`hotel_rooms`: `id` PK; `hotel_id` FK → `hotels.id`; `room_code` unique cùng hotel; `room_type`; `capacity` default 2; `assigned_user_ids` là TEXT chứa user ID phân cách dấu phẩy.

## Gala Dinner

### `gala_configs`

`id` PK; `event_id` FK unique; `is_enabled`; `lock_duration_seconds`; `turn_duration_seconds`; `turn_status` (`WAITING`, `ACTIVE`, `COMPLETED`); `current_turn_number`; `turn_started_at`; `rows`; `columns`; `created_at`; `updated_at`.

### `gala_seats`

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | VARCHAR | PK, UUID |
| `event_id` | VARCHAR | FK → `events.id` |
| `seat_code` | VARCHAR | Unique cùng Event |
| `table_code` | VARCHAR | Mã bàn |
| `seat_position` | INTEGER | Vị trí trong bàn |
| `status` | VARCHAR | `AVAILABLE`, `LOCKING`, `CONFIRMED`, `UNAVAILABLE` |
| `locked_by_team_id` | VARCHAR | FK legacy → `teams.id` |
| `locked_by_user_id` | VARCHAR | FK → `users.id`, người đang giữ ghế |
| `locked_at` | DATETIME | Thời điểm lock |
| `created_at`, `updated_at` | DATETIME | Audit thời gian |

### `gala_team_turns`

`id` PK; `event_id` FK; `team_id` FK; `turn_number`; `status` (`WAITING`, `ACTIVE`, `COMPLETED`, `SKIPPED`); `started_at`; `completed_at`.

Unique constraints: `(event_id, team_id)` và `(event_id, turn_number)`.

## `event_representatives`

Quyền đại diện theo Event + Team.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | VARCHAR | PK, UUID |
| `event_id` | VARCHAR | FK → `events.id` |
| `team_id` | VARCHAR | FK → `teams.id` |
| `user_id` | VARCHAR | FK → `users.id` |
| `created_at` | DATETIME | Thời gian tạo |

Unique constraints:

- `(event_id, team_id)`: mỗi Team/Event tối đa một representative.
- `(event_id, user_id)`: user không đại diện hai Team trong cùng Event.

## Các bảng phụ

### `event_schedules`

`id` PK; `event_id` FK; `schedule_time`; `title`; `description`; `location`; `display_order`; `created_at`; `updated_at`.

### `notifications`

`id` PK; `event_id` FK; `target_user_id` nullable FK; `target_team_id` nullable FK; `title`; `content`; `notification_type`; `created_by` FK; `created_at`.

### `user_notification_reads`

`id` PK; `user_id` FK; `notification_id` FK; `read_at`. Unique index `(user_id, notification_id)`.

### `refresh_tokens`

`id` PK; `user_id` FK; `token` unique/index; `expires_at`; `is_revoked`; `revoked_at`; `created_at`; `ip_address`; `user_agent`.

### `audit_logs`

`id` PK; `user_id`; `emp_code`; `action`; `entity_type`; `entity_id`; `old_data` JSON; `new_data` JSON; `reason`; `created_at`; `ip_address`; `user_agent`. Các field audit chính có index.

## Nâng cấp tự động khi backend khởi động

`init_db()` tự thêm nếu thiếu:

```text
registrations.team_id
registrations.assigned_outbound_flight_id
registrations.assigned_return_flight_id
gala_seats.locked_by_user_id
gala_configs.rows
gala_configs.columns
```

Với SQLite, code còn rebuild `registrations` nếu phát hiện unique index legacy chỉ trên `user_id`, để cho phép một user đăng ký nhiều Event.

## Nguyên tắc dữ liệu hiện tại

1. Resource phải gắn `event_id`.
2. Allocation luôn lọc theo `event_id`.
3. Flight allocation tách `OUTBOUND` và `RETURN`.
4. Representative mới được lưu ở `event_representatives`; `users.is_representative` chỉ là legacy.
5. Gala seat ownership mới dùng `locked_by_user_id`; `locked_by_team_id` giữ để tương thích.
6. Nên chuyển các nâng cấp trong `init_db()` sang Alembic migration trước khi production.