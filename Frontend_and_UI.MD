# FRONTEND & UI SPECIFICATION

**Dự án:** Team Building Portal – One-stop Portal  
**Stack bắt buộc:** React + TypeScript + Vite + Tailwind CSS  
**Data fetching:** TanStack React Query  
**Responsive:** Mobile-first, hỗ trợ mobile, tablet và desktop  
**Backend:** FastAPI, API prefix `/api/v1`, JWT Bearer

> Tài liệu này là blueprint để implement frontend. Tên field, enum và endpoint ưu tiên bám theo backend hiện tại. Không hard-code event, team, flight, vehicle, số ghế hoặc số chặng.

---

## 1. Mục tiêu và nguyên tắc UI

### 1.1. Mục tiêu

Frontend cần đáp ứng các mục tiêu sau:

- CBNV đăng nhập, đăng ký và xem toàn bộ hành trình Team Building trong một nền tảng.
- BTC/Admin quản lý dữ liệu, chuyến bay, xe, khách sạn, Gala Dinner và thông báo.
- Hỗ trợ auto allocation và manual adjustment.
- Hiển thị rõ ràng trạng thái đăng ký, trạng thái phân bổ và trạng thái công bố thông tin.
- Responsive trên mobile, tablet và desktop.
- Sử dụng Single Source of Truth từ backend.
- Không để người dùng hiểu nhầm giữa nguyện vọng cá nhân và kết quả phân bổ chính thức.

### 1.2. Nguyên tắc UX quan trọng

#### Nguyên tắc 1: Phân biệt nguyện vọng và kết quả chính thức

Frontend phải hiển thị riêng:

- `desired_shift`: Ca bay mong muốn.
- `allocated_flight_code`: Chuyến bay chính thức được phân bổ.
- Trạng thái allocation: Chưa phân bổ, đang phân bổ, đã phân bổ hoặc chưa thể phân bổ.

Không hiển thị ca mong muốn như thể đó là chuyến bay chính thức.

#### Nguyên tắc 2: Trạng thái Event quyết định quyền thao tác

| Backend status | Ý nghĩa | Hành vi frontend |
|---|---|---|
| `DRAFT` | Event đang cấu hình | Chỉ Admin được truy cập |
| `REGISTRATION_OPEN` | Đang mở đăng ký | CBNV được submit/update |
| `REGISTRATION_CLOSED` | Đã đóng đăng ký | Form chuyển sang read-only |
| `ALLOCATION_IN_PROGRESS` | Đang phân bổ | Hiển thị banner đang xử lý, disable chỉnh sửa |
| `ALLOCATION_COMPLETED` | Đã phân bổ xong | Admin rà soát kết quả |
| `EVENT_ACTIVE` | Sự kiện đang diễn ra | CBNV xem hành trình và lịch trình |
| `EVENT_COMPLETED` | Sự kiện đã kết thúc | Chỉ xem lại dữ liệu |

Frontend không được tự quyết định quyền nghiệp vụ. Backend vẫn là nguồn xác thực cuối cùng.

#### Nguyên tắc 3: Thao tác quan trọng phải có confirmation

Các thao tác cần confirmation modal:

- Hủy nhu cầu xe.
- Xóa event.
- Xóa team.
- Xóa chuyến bay.
- Xóa xe.
- Xóa/reset ghế Gala.
- Clear allocation.
- Disable Gala Dinner.
- Thay đổi trạng thái event.

Modal phải nói rõ hậu quả của thao tác.

#### Nguyên tắc 4: Mọi mutation phải có feedback

Mọi thao tác POST, PUT, DELETE phải có:

- Loading state trên button.
- Disable button để chống double-submit.
- Toast hoặc success message.
- Error message nếu thất bại.
- Refetch hoặc invalidate query liên quan.

#### Nguyên tắc 5: Không sử dụng `alert()` native trong production

Thay thế `alert()` bằng:

- `Toast`: thông báo ngắn.
- `InlineError`: lỗi ngay dưới field hoặc component.
- `AlertBanner`: cảnh báo quan trọng.
- `ConfirmDialog`: xác nhận thao tác nguy hiểm.

#### Nguyên tắc 6: Format ngày giờ thống nhất

- Backend trả ngày giờ theo ISO8601.
- Frontend format theo locale `vi-VN`.
- Không tự ý thay đổi timezone.
- Tạo utility dùng chung:

```ts
formatDate(value)
formatDateTime(value)
formatTime(value)
formatRelativeTime(value)
```

---

## 2. Kiến trúc Frontend

### 2.1. Công nghệ sử dụng

Các công nghệ chính:

- React.
- TypeScript.
- Vite.
- React Router.
- Tailwind CSS.
- TanStack React Query.
- Axios.

Có thể sử dụng thêm thư viện icon, form validation hoặc chart nếu cần. Tuy nhiên cần thống nhất một thư viện duy nhất cho từng mục đích, tránh trộn quá nhiều UI library.

### 2.2. Cấu trúc thư mục đề xuất

```text
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
├── .env.example
├── Dockerfile
├── nginx.conf
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    │
    ├── routes/
    │   ├── AppRoutes.tsx
    │   ├── ProtectedRoute.tsx
    │   ├── AdminRoute.tsx
    │   └── RepresentativeRoute.tsx
    │
    ├── api/
    │   ├── httpClient.ts
    │   ├── authApi.ts
    │   ├── userApi.ts
    │   ├── eventApi.ts
    │   ├── registrationApi.ts
    │   ├── journeyApi.ts
    │   ├── galaApi.ts
    │   ├── adminApi.ts
    │   ├── allocationApi.ts
    │   └── notificationApi.ts
    │
    ├── types/
    │   ├── auth.ts
    │   ├── user.ts
    │   ├── event.ts
    │   ├── registration.ts
    │   ├── resource.ts
    │   ├── journey.ts
    │   ├── gala.ts
    │   ├── allocation.ts
    │   └── admin.ts
    │
    ├── hooks/
    │   ├── useAuth.ts
    │   ├── useCurrentUser.ts
    │   ├── useActiveEvent.ts
    │   ├── useRegistration.ts
    │   ├── useJourney.ts
    │   ├── useGalaSeats.ts
    │   └── useAdminStats.ts
    │
    ├── layouts/
    │   ├── AuthLayout.tsx
    │   ├── AppLayout.tsx
    │   └── AdminLayout.tsx
    │
    ├── components/
    │   ├── ui/
    │   │   ├── Button.tsx
    │   │   ├── Input.tsx
    │   │   ├── Select.tsx
    │   │   ├── Textarea.tsx
    │   │   ├── Checkbox.tsx
    │   │   ├── RadioCard.tsx
    │   │   ├── Badge.tsx
    │   │   ├── Card.tsx
    │   │   ├── Modal.tsx
    │   │   ├── ConfirmDialog.tsx
    │   │   ├── Toast.tsx
    │   │   ├── Tabs.tsx
    │   │   ├── ProgressBar.tsx
    │   │   └── DataTable.tsx
    │   │
    │   ├── layout/
    │   │   ├── Header.tsx
    │   │   ├── Sidebar.tsx
    │   │   ├── MobileMenu.tsx
    │   │   ├── BottomNavigation.tsx
    │   │   └── Breadcrumb.tsx
    │   │
    │   ├── feedback/
    │   │   ├── PageLoader.tsx
    │   │   ├── Skeleton.tsx
    │   │   ├── ErrorState.tsx
    │   │   ├── EmptyState.tsx
    │   │   └── AccessDenied.tsx
    │   │
    │   ├── registration/
    │   │   ├── PersonalInfoCard.tsx
    │   │   ├── ParticipationSelector.tsx
    │   │   ├── ShiftSelector.tsx
    │   │   ├── VehicleRouteCard.tsx
    │   │   ├── TermsAgreement.tsx
    │   │   ├── RegistrationReview.tsx
    │   │   └── CancelVehicleDialog.tsx
    │   │
    │   ├── journey/
    │   │   ├── JourneyHeader.tsx
    │   │   ├── JourneyTimeline.tsx
    │   │   ├── FlightCard.tsx
    │   │   ├── VehicleCard.tsx
    │   │   ├── HotelCard.tsx
    │   │   ├── GalaCard.tsx
    │   │   ├── ScheduleList.tsx
    │   │   └── NotificationList.tsx
    │   │
    │   ├── gala/
    │   │   ├── GalaHeader.tsx
    │   │   ├── GalaLegend.tsx
    │   │   ├── GalaStage.tsx
    │   │   ├── GalaTable.tsx
    │   │   ├── GalaSeat.tsx
    │   │   ├── GalaSeatSummary.tsx
    │   │   └── GalaCountdown.tsx
    │   │
    │   └── admin/
    │       ├── StatCard.tsx
    │       ├── EventStatusBadge.tsx
    │       ├── AllocationResultCard.tsx
    │       ├── CapacityIndicator.tsx
    │       ├── ImportDropzone.tsx
    │       ├── AdminTable.tsx
    │       └── FilterBar.tsx
    │
    ├── pages/
    │   ├── LoginPage.tsx
    │   ├── NotFoundPage.tsx
    │   ├── TermsPage.tsx
    │   ├── user/
    │   │   ├── JourneyPage.tsx
    │   │   ├── RegistrationPage.tsx
    │   │   └── GalaPage.tsx
    │   └── admin/
    │       ├── AdminDashboardPage.tsx
    │       ├── EventsPage.tsx
    │       ├── TeamsPage.tsx
    │       ├── UsersPage.tsx
    │       ├── FlightsPage.tsx
    │       ├── VehiclesPage.tsx
    │       ├── FlightAllocationPage.tsx
    │       ├── VehicleAllocationPage.tsx
    │       ├── HotelsPage.tsx
    │       ├── GalaAdminPage.tsx
    │       ├── NotificationsPage.tsx
    │       └── AuditLogsPage.tsx
    │
    ├── stores/
    │   ├── authStore.ts
    │   └── uiStore.ts
    │
    ├── utils/
    │   ├── date.ts
    │   ├── enumLabels.ts
    │   ├── error.ts
    │   ├── permissions.ts
    │   ├── download.ts
    │   └── validation.ts
    │
    └── constants/
        ├── routes.ts
        ├── queryKeys.ts
        └── ui.ts
```

### 2.3. Quy tắc phân lớp

#### `api/`

Chỉ chịu trách nhiệm gọi API:

- Không viết JSX.
- Không chứa logic hiển thị.
- Không truy cập trực tiếp trong component.

#### `types/`

Chứa TypeScript type mirror với Pydantic schema của backend.

#### `hooks/`

Chứa:

- React Query.
- Query key.
- Mutation.
- Invalidation.
- Loading/error state.

#### `components/`

Chứa component tái sử dụng.

#### `pages/`

Chứa logic composition cho từng màn hình.

#### `layouts/`

Chứa app shell, sidebar, header, mobile navigation.

#### `stores/`

Chỉ chứa client state như:

- Auth session.
- Menu mobile.
- Theme.
- Toast.
- Filter UI.

Server state phải được quản lý bởi React Query, không lưu trùng trong global store.

---

## 3. TypeScript Models

### 3.1. Enum chính

```ts
export type Role =
  | 'USER'
  | 'ADMIN'
  | 'TEAM_REPRESENTATIVE'
  | 'SUPER_ADMIN';

export type EventStatus =
  | 'DRAFT'
  | 'REGISTRATION_OPEN'
  | 'REGISTRATION_CLOSED'
  | 'ALLOCATION_IN_PROGRESS'
  | 'ALLOCATION_COMPLETED'
  | 'EVENT_ACTIVE'
  | 'EVENT_COMPLETED';

export type DesiredShift = 'SHIFT_1' | 'SHIFT_2';

export type FlightDirection = 'OUTBOUND' | 'RETURN';

export type RouteType =
  | 'ROUTE_1'
  | 'ROUTE_2'
  | 'ROUTE_3'
  | 'ROUTE_4';

export type SeatStatus =
  | 'AVAILABLE'
  | 'LOCKING'
  | 'CONFIRMED'
  | 'UNAVAILABLE';

export type GalaTurnStatus =
  | 'WAITING'
  | 'ACTIVE'
  | 'COMPLETED'
  | 'SKIPPED';

export type NotificationType =
  | 'INFO'
  | 'WARNING'
  | 'URGENT';
```

### 3.2. Authentication types

```ts
export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: string;
  emp_code: string;
  full_name: string;
  roles: Role[];
}

export interface JwtPayload {
  sub: string;
  emp_code: string;
  team_id?: string | null;
  active_event_id?: string | null;
  roles: Role[];
  exp: number;
  type: 'access' | 'refresh';
}
```

### 3.3. Registration types

```ts
export interface RegistrationForm {
  is_participating: boolean;
  desired_shift: DesiredShift | null;

  needs_vehicle_route_1: boolean;
  needs_vehicle_route_2: boolean;
  needs_vehicle_route_3: boolean;
  needs_vehicle_route_4: boolean;

  pickup_location_route_1: string | null;
  pickup_location_route_4: string | null;

  comments: string | null;
  agreed_to_terms: boolean;
}

export interface RegistrationUpdateRequest {
  desired_shift?: DesiredShift | null;

  needs_vehicle_route_1?: boolean;
  needs_vehicle_route_2?: boolean;
  needs_vehicle_route_3?: boolean;
  needs_vehicle_route_4?: boolean;

  pickup_location_route_1?: string | null;
  pickup_location_route_4?: string | null;

  comments?: string | null;
}

export interface RegistrationResponse extends RegistrationForm {
  id: string;
  user_id: string;
  event_id: string;

  allocated_flight_id?: string | null;
  allocated_flight_code?: string | null;

  allocated_vehicle_1_id?: string | null;
  allocated_vehicle_2_id?: string | null;
  allocated_vehicle_3_id?: string | null;
  allocated_vehicle_4_id?: string | null;

  hotel_room_code?: string | null;
}
```

### 3.4. Journey types

```ts
export interface JourneyFlightInfo {
  flight_code: string;
  direction: 'OUTBOUND' | 'RETURN';
  departure_time: string;
  arrival_time: string;
  origin: string;
  destination: string;
}

export interface JourneyVehicleInfo {
  vehicle_name: string;
  route_type: RouteType;
  departure_time: string;
  pickup_location: string;
  dropoff_location?: string | null;
  captain_name?: string | null;
  captain_phone?: string | null;
  notes?: string | null;
}

export interface JourneyHotelInfo {
  hotel_name: string;
  address?: string | null;
  phone?: string | null;
  room_code: string;
  room_type?: string | null;
  roommates: string[];
}

export interface JourneyGalaInfo {
  seat_code: string;
  table_code?: string | null;
  seat_position?: number | null;
  status: string;
}

export interface EventScheduleItem {
  time: string;
  title: string;
  description?: string | null;
  location?: string | null;
}

export interface NotificationItem {
  id: string;
  title: string;
  content: string;
  notification_type: NotificationType;
  created_at: string;
  is_read: boolean;
}

export interface MyJourneyResponse {
  user_name: string;
  emp_code: string;
  email: string;
  phone?: string | null;

  team_name?: string | null;
  team_leader?: string | null;

  event_name: string;
  event_date_start: string;
  event_date_end: string;
  event_location: string;
  event_status: EventStatus;

  is_participating: boolean;
  registration_status: string;

  outbound_flight?: JourneyFlightInfo | null;
  return_flight?: JourneyFlightInfo | null;

  vehicles: JourneyVehicleInfo[];

  hotel?: JourneyHotelInfo | null;

  gala_seat?: JourneyGalaInfo | null;

  schedule: EventScheduleItem[];
  notifications: NotificationItem[];

  last_updated: string;
}
```

### 3.5. Gala types

```ts
export interface GalaSeatResponse {
  id: string;
  event_id: string;
  seat_code: string;
  table_code?: string | null;
  seat_position?: number | null;
  status: SeatStatus;
  locked_by_team_id?: string | null;
  locked_at?: string | null;
}

export interface GalaSeatingLayout {
  event_id: string;
  seats: GalaSeatResponse[];

  total_seats: number;
  available_seats: number;
  locked_seats: number;
  confirmed_seats: number;
  unavailable_seats: number;

  stage_position: string;
}

export interface GalaConfigResponse {
  id: string;
  event_id: string;
  is_enabled: boolean;
  lock_duration_seconds: number;
  turn_duration_seconds: number;
  turn_status: GalaTurnStatus;
  current_turn_number?: number | null;
  turn_started_at?: string | null;
}

export interface GalaTeamTurnResponse {
  id: string;
  event_id: string;
  team_id: string;
  team_name?: string | null;
  turn_number: number;
  status: GalaTurnStatus;
  valid_member_count: number;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface SeatLockRequest {
  seat_codes: string[];
}

export interface SeatConfirmRequest {
  seat_codes: string[];
}

export interface SeatReleaseRequest {
  seat_codes: string[];
}
```

---

## 4. API Client

### 4.1. Base URL

```env
VITE_API_URL=/api/v1
```

Local development có thể dùng:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

Docker/Nginx nên sử dụng:

```env
VITE_API_URL=/api/v1
```

### 4.2. Axios instance

File:

```text
src/api/httpClient.ts
```

Yêu cầu:

- Tạo Axios instance.
- Tự động thêm access token.
- Xử lý refresh token khi gặp 401.
- Không refresh nhiều lần đồng thời.
- Nếu refresh thất bại thì clear session và chuyển `/login`.

Pseudo-code:

```ts
import axios from 'axios';

const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

httpClient.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem('access_token');

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  return config;
});
```

### 4.3. Quy tắc xử lý token

- Access token có thời hạn ngắn.
- Refresh token dùng để lấy access token mới.
- Không log token.
- Không lưu password.
- Không decode JWT để quyết định quyền bảo mật.
- Backend vẫn phải kiểm tra role.
- Nếu có thể, production nên dùng HttpOnly Secure cookie cho refresh token.

### 4.4. API mapping

#### Auth

```text
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/users/me
```

#### User registration

```text
GET  /api/v1/registrations/me
POST /api/v1/registrations/submit
PUT  /api/v1/registrations/update
POST /api/v1/registrations/cancel-vehicle
```

#### Journey

```text
GET  /api/v1/journey/me
GET  /api/v1/journey/summary
POST /api/v1/journey/notifications/{notification_id}/read
```

#### Gala

```text
GET  /api/v1/gala/seats
POST /api/v1/gala/lock
POST /api/v1/gala/confirm
POST /api/v1/gala/release
```

#### Admin resources

```text
GET/POST/PUT/DELETE /api/v1/admin/events
GET/POST/PUT/DELETE /api/v1/admin/teams
GET/POST/PUT/DELETE /api/v1/admin/resources/flights
GET/POST/PUT/DELETE /api/v1/admin/vehicles
```

#### Admin allocation

```text
POST   /api/v1/admin/allocations/flights/auto
PUT    /api/v1/admin/allocations/flights/manual
GET    /api/v1/admin/allocations/flights/results
GET    /api/v1/admin/allocations/flights/stats
DELETE /api/v1/admin/allocations/flights/clear

POST   /api/v1/admin/allocations/vehicles/auto
PUT    /api/v1/admin/allocations/vehicles/manual
GET    /api/v1/admin/allocations/vehicles/results
DELETE /api/v1/admin/allocations/vehicles/clear
```

#### Hotels

```text
POST /api/v1/admin/hotels/import-rooms
GET  /api/v1/admin/hotels/export-template
GET  /api/v1/admin/hotels
```

#### Admin dashboard

```text
GET /api/v1/admin/dashboard/stats
GET /api/v1/admin/dashboard/statistics/{event_id}
GET /api/v1/admin/dashboard/teams/{event_id}
GET /api/v1/admin/dashboard/users/{event_id}
```

---

## 5. React Query

### 5.1. Query keys

```ts
export const queryKeys = {
  me: ['users', 'me'] as const,

  activeEvent: ['events', 'active'] as const,

  registration: ['registrations', 'me'] as const,

  journey: ['journey', 'me'] as const,

  journeySummary: ['journey', 'summary'] as const,

  galaSeats: (eventId: string) =>
    ['gala', 'seats', eventId] as const,

  galaConfig: (eventId: string) =>
    ['admin', 'gala', 'config', eventId] as const,

  adminStats: (eventId?: string) =>
    ['admin', 'dashboard', 'stats', eventId] as const,

  flights: (eventId: string) =>
    ['admin', 'flights', eventId] as const,

  vehicles: (eventId: string, routeType?: RouteType) =>
    ['admin', 'vehicles', eventId, routeType] as const,
};
```

### 5.2. Invalidation rules

Sau khi submit registration:

```ts
queryClient.invalidateQueries({
  queryKey: queryKeys.registration,
});

queryClient.invalidateQueries({
  queryKey: queryKeys.journey,
});

queryClient.invalidateQueries({
  queryKey: queryKeys.journeySummary,
});
```

Sau khi update registration:

- Invalidate registration.
- Invalidate journey.
- Invalidate journey summary.

Sau khi cancel vehicle:

- Invalidate registration.
- Invalidate journey.
- Invalidate vehicle-related queries nếu đang ở Admin.

Sau khi lock seat:

- Refetch gala seats ngay lập tức.

Sau khi confirm/release seat:

- Refetch gala seats.
- Invalidate journey.

### 5.3. Retry policy

Không retry tự động với:

- 400.
- 401.
- 403.
- 409.
- 422.

Chỉ retry giới hạn với:

- Network error.
- HTTP 5xx.
- GET request idempotent.

Không tự động retry mutation submit registration để tránh tạo dữ liệu trùng.

---

## 6. Routing

### 6.1. User routes

| Route | Màn hình | Quyền |
|---|---|---|
| `/login` | Đăng nhập | Public |
| `/` | Redirect theo role | Auth |
| `/journey` | My Team Building Journey | Auth |
| `/registration` | Form đăng ký | Auth |
| `/gala` | Chọn ghế Gala | Team Representative |
| `/terms` | Điều khoản | Public/Auth |
| `*` | Not Found | Any |

### 6.2. Admin routes

| Route | Màn hình |
|---|---|
| `/admin` | Dashboard |
| `/admin/events` | Quản lý Event |
| `/admin/teams` | Quản lý Team |
| `/admin/users` | Danh sách CBNV |
| `/admin/flights` | Quản lý chuyến bay |
| `/admin/vehicles` | Quản lý xe |
| `/admin/allocations/flights` | Phân bổ chuyến bay |
| `/admin/allocations/vehicles` | Phân bổ xe |
| `/admin/hotels` | Import phòng |
| `/admin/gala` | Cấu hình Gala |
| `/admin/notifications` | Quản lý thông báo |
| `/admin/audit-logs` | Audit log |

### 6.3. Route guards

#### `ProtectedRoute`

Kiểm tra:

- Có access token hay không.
- Session có đang hydrate hay không.
- Nếu chưa login thì chuyển `/login`.

#### `AdminRoute`

Kiểm tra role:

```ts
const isAdmin =
  roles.includes('ADMIN') ||
  roles.includes('SUPER_ADMIN');
```

Nếu không có quyền:

- Không render admin page.
- Hiển thị `AccessDenied`.
- Không chỉ dựa vào việc ẩn menu.

#### `RepresentativeRoute`

Kiểm tra role `TEAM_REPRESENTATIVE`.

Người không có quyền cần thấy thông báo:

> Bạn không được phân quyền đại diện Team để thực hiện chọn ghế Gala Dinner.

---

## 7. Layout và Responsive UI

### 7.1. Desktop layout

- Sidebar trái rộng khoảng 240–280px.
- Header trên cùng.
- Main content có max-width khoảng 1440px.
- Nội dung dùng padding:

```text
p-4 sm:p-6 lg:p-8
```

### 7.2. Mobile layout

- Header cố định.
- Menu chuyển thành drawer.
- Có thể dùng bottom navigation cho các chức năng chính.
- Sidebar desktop được ẩn ở breakpoint nhỏ.
- Các action chính có thể dùng sticky bottom action bar.
- Không để toàn bộ trang bị overflow ngang.

### 7.3. Header

Header gồm:

- Logo/tên portal.
- Tên event hiện tại.
- Badge trạng thái event.
- Notification badge.
- User menu.
- Nút mở mobile menu.

### 7.4. Sidebar

User menu:

- My Journey.
- Đăng ký.
- Gala Dinner nếu có quyền.
- Điều khoản.
- Đăng xuất.

Admin menu:

- Dashboard.
- Events.
- Teams.
- Users.
- Flights.
- Vehicles.
- Allocations.
- Hotels.
- Gala.
- Notifications.
- Audit logs.

---

## 8. Tailwind Design System

### 8.1. Màu sắc

Gợi ý:

```text
Primary: blue-600
Primary hover: blue-700
Success: emerald-600
Warning: amber-500
Danger: red-600
Info: sky-600
Text primary: slate-900
Text secondary: slate-600
Border: slate-200
Background: slate-50
```

### 8.2. Component style

Card:

```text
rounded-xl border border-slate-200 bg-white shadow-sm
```

Button primary:

```text
rounded-lg bg-blue-600 px-4 py-2.5
text-white hover:bg-blue-700
focus-visible:outline-none focus-visible:ring-2
focus-visible:ring-blue-500
disabled:cursor-not-allowed disabled:opacity-50
```

Input:

```text
w-full rounded-lg border border-slate-300
px-3 py-2.5
focus:border-blue-500
focus:outline-none
focus:ring-2
focus:ring-blue-500/20
```

### 8.3. Touch target

Mọi button và control trên mobile nên có kích thước tối thiểu:

```text
min-h-[44px] min-w-[44px]
```

### 8.4. Breakpoints

| Breakpoint | Sử dụng |
|---|---|
| `sm` | Chia form thành hai cột nếu đủ rộng |
| `md` | Hiển thị sidebar và bảng desktop |
| `lg` | Dashboard nhiều cột |
| `xl` | Layout màn hình lớn |

---

## 9. Login Page

### 9.1. UI

Màn hình gồm:

- Logo.
- Tên hệ thống.
- Tiêu đề “Đăng nhập Team Building Portal”.
- Email công ty.
- Password.
- Nút show/hide password.
- Nút đăng nhập.
- Loading state.
- Error message.
- SSO button nếu backend hỗ trợ.

### 9.2. Validation

Frontend kiểm tra:

- Email đúng định dạng.
- Password tối thiểu 6 ký tự.

Backend vẫn là nơi xác thực cuối cùng.

### 9.3. Flow

```text
POST /auth/login
    ↓
Lưu access_token và refresh_token
    ↓
GET /users/me
    ↓
GET /events/active
    ↓
Redirect theo role
```

Redirect:

- Admin → `/admin`.
- User → `/journey`.
- Team Representative → `/journey`.

Không hiển thị thông tin quá chi tiết khiến người dùng biết email nào tồn tại trong hệ thống.

---

## 10. Registration Page

### 10.1. Mục tiêu

Cho CBNV:

- Xác nhận tham gia.
- Chọn ca bay mong muốn.
- Đăng ký nhu cầu xe cho 4 chặng.
- Chọn điểm đón/trả nếu có.
- Nhập mong muốn.
- Đồng ý điều khoản.
- Xem lại và submit.
- Cập nhật thông tin khi registration còn mở.
- Hủy nhu cầu xe sau khi được phân bổ nếu business cho phép.

### 10.2. Cấu trúc màn hình

#### Section 1: Thông tin cá nhân

Hiển thị read-only:

- Họ và tên.
- Email.
- Mã nhân viên.
- Team/Bộ phận.
- Địa điểm làm việc.
- Số điện thoại.

Nguồn dữ liệu:

```text
GET /api/v1/users/me
```

Không cho CBNV chỉnh sửa các thông tin master data ở form đăng ký.

#### Section 2: Xác nhận tham gia

Radio:

- Có tham gia.
- Không tham gia.

Nếu chọn “Không tham gia”:

- Có thể ẩn hoặc disable phần ca bay.
- Disable nhu cầu xe.
- Hiển thị thông báo giải thích.
- Submit với:

```json
{
  "is_participating": false
}
```

#### Section 3: Điều khoản

Checkbox:

```text
agreed_to_terms
```

Nội dung phải giải thích:

- Đã đọc và đồng ý quy định chương trình.
- Chính sách/phí phạt nếu hủy sai quy định.
- Hủy xe sát giờ có thể không hoàn tác.
- Hủy xe không chạy lại Auto Allocation.
- Ca đăng ký chỉ là nguyện vọng, không đảm bảo 100%.

Checkbox bắt buộc với registration mới.

#### Section 4: Chọn ca bay mong muốn

Hiển thị bằng hai Radio Card:

```text
SHIFT_1: Ca trước 17:00
SHIFT_2: Ca sau 17:00
```

Chú thích bắt buộc:

> Đây chỉ là nguyện vọng đăng ký. BTC sẽ phân bổ dựa trên nguồn lực và quy tắc chung, không cam kết đáp ứng 100%.

#### Section 5: Nhu cầu xe

Hiển thị 4 route card:

| Route | Nội dung |
|---|---|
| Route 1 | Văn phòng HN/HCM → Sân bay |
| Route 2 | Sân bay → Khách sạn |
| Route 3 | Khách sạn → Sân bay |
| Route 4 | Sân bay → Văn phòng HN/HCM |

Mỗi route có:

- Toggle Có/Không.
- Mô tả route.
- Điểm đón nếu có.
- Điểm trả nếu có.
- Ghi chú cần thiết.

Field tương ứng:

```text
needs_vehicle_route_1
needs_vehicle_route_2
needs_vehicle_route_3
needs_vehicle_route_4
pickup_location_route_1
pickup_location_route_4
```

#### Section 6: Mong muốn/đề xuất

Textarea:

```text
comments
```

- Tối đa 1000 ký tự.
- Có character counter.
- Placeholder thân thiện.
- Hiển thị rõ đây là đề xuất, không mặc định được đáp ứng.

#### Section 7: Review

Trước khi submit, hiển thị summary:

- Trạng thái tham gia.
- Ca mong muốn.
- 4 route xe.
- Điểm đón/trả.
- Mong muốn.
- Trạng thái đồng ý điều khoản.

Nút:

- Quay lại.
- Xác nhận đăng ký.

### 10.3. API

Khi mở trang:

```text
GET /api/v1/registrations/me
```

Đăng ký mới:

```text
POST /api/v1/registrations/submit
```

Cập nhật:

```text
PUT /api/v1/registrations/update
```

Hủy xe:

```text
POST /api/v1/registrations/cancel-vehicle
```

Request:

```json
{
  "route_number": 1,
  "reason": "Tự di chuyển"
}
```

### 10.4. Read-only mode

Form chuyển sang read-only khi:

- Event status là `REGISTRATION_CLOSED`.
- Event status là `ALLOCATION_IN_PROGRESS`.
- Backend trả lỗi registration đã đóng.

UI cần:

- Disable input.
- Disable submit button.
- Hiển thị banner:

> Đăng ký đã đóng. Bạn chỉ có thể xem lại thông tin đã gửi.

### 10.5. Success state

Sau submit thành công:

- Hiển thị success panel.
- Hiển thị trạng thái registration.
- Hiển thị thông báo email xác nhận.
- Có link “Xem hành trình”.
- Refetch registration và journey.

### 10.6. Hủy xe

Chỉ hiển thị nút hủy ở route phù hợp.

Confirmation modal:

> Bạn có chắc muốn hủy nhu cầu xe cho chặng này không? Thao tác có thể không hoàn tác và hệ thống sẽ không chạy lại Auto Allocation.

Sau thành công:

- Hiển thị toast.
- Refetch registration.
- Refetch journey.
- Cập nhật trạng thái route.

---

## 11. Journey Page

### 11.1. API

```text
GET /api/v1/journey/me
```

### 11.2. Journey Header

Hiển thị:

- Tên sự kiện.
- Ngày bắt đầu/kết thúc.
- Địa điểm.
- Event status.
- Last updated.
- Nút refresh thủ công.

### 11.3. Profile Card

Hiển thị:

- Họ tên.
- Mã nhân viên.
- Email.
- Số điện thoại.
- Team.
- Team leader.

### 11.4. Registration Card

Hiển thị:

- Có/không tham gia.
- Registration status.
- Ca mong muốn.
- Trạng thái phân bổ.

### 11.5. Timeline

Timeline nên hiển thị các mốc:

1. Đăng ký.
2. Chuyến bay đi.
3. Xe Route 1.
4. Xe Route 2.
5. Khách sạn.
6. Gala Dinner.
7. Xe Route 3.
8. Chuyến bay về.
9. Xe Route 4.
10. Các hoạt động theo `schedule`.

Timeline trên mobile:

- Một cột dọc.
- Icon ở bên trái.
- Nội dung bên phải.
- Không dùng layout ngang gây overflow.

Timeline trên desktop:

- Có thể dùng timeline dọc hoặc hai cột.

### 11.6. Flight Card

Hiển thị:

- Direction: Đi/Về.
- Flight code.
- Origin.
- Destination.
- Departure time.
- Arrival time.
- Trạng thái phân bổ.

Nếu chưa có dữ liệu:

> BTC chưa công bố thông tin chuyến bay.

### 11.7. Vehicle Card

Mỗi vehicle card hiển thị:

- Route.
- Tên xe.
- Giờ tập trung/khởi hành.
- Điểm đón.
- Điểm trả.
- Tên trưởng xe.
- Số điện thoại trưởng xe.
- Ghi chú.

Số điện thoại trên mobile có thể dùng:

```html
<a href="tel:+849xxxxxxxx">Gọi trưởng xe</a>
```

### 11.8. Hotel Card

Hiển thị:

- Tên khách sạn.
- Địa chỉ.
- Số điện thoại.
- Mã phòng.
- Loại phòng.
- Danh sách người ở cùng.

Nếu chưa công bố:

> BTC chưa công bố thông tin phòng.

### 11.9. Gala Card

Hiển thị:

- Bàn.
- Ghế.
- Vị trí ghế.
- Trạng thái.
- Link đến `/gala` nếu user có quyền đại diện Team.

### 11.10. Schedule

Hiển thị:

- Thời gian.
- Tên hoạt động.
- Mô tả.
- Địa điểm.

### 11.11. Notification

Hiển thị:

- Tiêu đề.
- Nội dung.
- Loại INFO/WARNING/URGENT.
- Thời gian.
- Trạng thái đã đọc/chưa đọc.

Mark as read:

```text
POST /api/v1/journey/notifications/{notification_id}/read
```

### 11.12. Empty và error state

Nếu API thành công nhưng thiếu dữ liệu:

- Không hiển thị skeleton vô hạn.
- Hiển thị empty state theo từng section.
- Nói rõ “chưa công bố” hoặc “chưa phân bổ”.

Nếu API lỗi:

- Hiển thị error state.
- Có nút Retry.
- Không làm mất các dữ liệu cũ đang có nếu refetch thất bại.

---

## 12. Gala Dinner Seat Selection

### 12.1. Quyền

Chỉ user có role:

```text
TEAM_REPRESENTATIVE
```

được chọn ghế.

Backend không nhận `team_id` từ frontend. Backend lấy team từ JWT và kiểm tra lại database.

### 12.2. API

Lấy sơ đồ:

```text
GET /api/v1/gala/seats
```

Lock:

```text
POST /api/v1/gala/lock
```

Request:

```json
{
  "seat_codes": ["A1", "A2", "A3"]
}
```

Confirm:

```text
POST /api/v1/gala/confirm
```

Release:

```text
POST /api/v1/gala/release
```

### 12.3. Polling

Sử dụng React Query:

- Refetch mỗi 2–3 giây.
- Đề xuất 3 giây.
- Dừng khi tab bị hidden.
- Dừng khi component unmount.
- Dừng khi turn đã hoàn tất.
- Không polling khi chưa có token.

Pseudo configuration:

```ts
refetchInterval: 3000,
refetchIntervalInBackground: false,
```

### 12.4. Layout

Màn hình gồm:

1. Gala header.
2. Team turn status.
3. Countdown.
4. Legend.
5. Stage.
6. Danh sách bàn.
7. Seat map.
8. Selected seat summary.
9. Nút lock/confirm/release.

### 12.5. Seat legend

| Status | Màu gợi ý | Ý nghĩa |
|---|---|---|
| `AVAILABLE` | Xanh | Ghế có thể chọn |
| `LOCKING` | Vàng | Đang được Team thao tác |
| `CONFIRMED` | Xanh đậm/đỏ | Đã xác nhận |
| `UNAVAILABLE` | Xám | Không khả dụng |

Không chỉ dùng màu. Mỗi seat cần có text/aria label.

### 12.6. Seat selection rules

- Chỉ được chọn seat `AVAILABLE`.
- Không được chọn quá `valid_member_count`.
- Không cho chọn trùng seat.
- Seat code normalize uppercase.
- Hiển thị số ghế đã chọn/tổng số thành viên hợp lệ.

### 12.7. Lock flow

```text
User chọn ghế
    ↓
POST /gala/lock
    ↓
Backend kiểm tra optimistic locking
    ↓
Nếu thành công → bắt đầu countdown lock
    ↓
Nếu thất bại 409 → refetch và thông báo
```

Không gửi:

```json
{
  "team_id": "..."
}
```

### 12.8. Confirm flow

Sau khi lock thành công:

- Hiển thị countdown lock duration.
- Hiển thị các seat đang lock bởi Team.
- Nút “Xác nhận ghế”.
- Nút “Bỏ chọn/Release”.

Khi confirm:

```json
{
  "seat_codes": ["A1", "A2"]
}
```

Chỉ cập nhật giao diện thành confirmed sau khi backend trả thành công.

### 12.9. Xử lý lỗi 409

Thông báo:

> Một hoặc nhiều ghế vừa được Team khác chọn. Sơ đồ ghế đã được cập nhật, vui lòng chọn lại.

Sau đó:

- Xóa seat không còn available khỏi local selection.
- Refetch ngay.
- Không tự động gửi lại request lock.

### 12.10. Hết thời gian lock

Khi countdown về 0:

- Clear local selected seats.
- Refetch layout.
- Hiển thị thông báo hết thời gian giữ ghế.
- Có thể gọi release nếu backend yêu cầu.

---

## 13. Admin Dashboard

### 13.1. KPI Cards

Hiển thị:

- Tổng số CBNV.
- Đã đăng ký.
- Chưa đăng ký.
- Số người tham gia.
- Số người không tham gia.
- Số đăng ký SHIFT_1.
- Số đăng ký SHIFT_2.
- Nhu cầu xe theo từng route.
- Flight capacity.
- Vehicle capacity.
- Hotel assignment status.
- Gala status.

### 13.2. Quick Actions

Các action nhanh:

- Tạo event.
- Quản lý team.
- Thêm chuyến bay.
- Thêm xe.
- Chạy auto flight allocation.
- Chạy auto vehicle allocation.
- Import phòng.
- Tạo notification.
- Export registration.

### 13.3. Chart

Nếu dùng chart:

- Chart phải có fallback dạng bảng.
- Không chỉ dùng màu để phân biệt.
- Có title và aria label.
- Có trạng thái empty nếu chưa có dữ liệu.

---

## 14. Event Management

### 14.1. Danh sách event

Các chức năng:

- Search theo tên event.
- Filter status.
- Sort theo ngày.
- Pagination.
- Create.
- Edit.
- Delete.
- Chuyển trạng thái.

### 14.2. Event form

Field:

- `event_name`
- `event_date_start`
- `event_date_end`
- `location`
- `registration_deadline`
- `description`
- `status`

Validation:

- Tên không rỗng.
- Ngày kết thúc không trước ngày bắt đầu.
- Deadline đăng ký hợp lệ.
- Status transition phải được backend chấp nhận.

### 14.3. Status transition

Khi chuyển trạng thái:

- Hiển thị modal.
- Nêu rõ ảnh hưởng.
- Backend là nơi xác định transition hợp lệ.
- Nếu backend trả lỗi thì hiển thị lý do.

---

## 15. Team Management

### 15.1. UI

- Danh sách Team.
- Search.
- Filter theo event.
- Create.
- Edit.
- Delete.
- Hiển thị số lượng thành viên.

### 15.2. Validation

- Không cho trùng team name trong cùng event.
- Delete phải cảnh báo nếu Team đang có user/registration.
- Không cho nhập tên tùy ý ở form CBNV nếu đó là master data.

---

## 16. User và Registration Management

### 16.1. Danh sách CBNV

Search theo:

- Họ tên.
- Mã nhân viên.
- Email.
- Team.

Filter:

- Có/không tham gia.
- Ca mong muốn.
- Registration status.
- Flight allocation.
- Vehicle allocation.
- Hotel allocation.

### 16.2. Mobile

Desktop có thể sử dụng table.

Mobile nên chuyển thành card:

```text
EmployeeCard
├── Họ tên
├── Mã nhân viên
├── Team
├── Trạng thái đăng ký
├── Chuyến bay
└── Action menu
```

---

## 17. Flight Management

### 17.1. Flight form

Field:

- Event.
- Flight code.
- Direction.
- Total slots.
- Departure time.
- Arrival time.
- Origin.
- Destination.

### 17.2. Flight table

Hiển thị:

- Flight code.
- Direction.
- Departure.
- Arrival.
- Origin.
- Destination.
- Total slots.
- Assigned count.
- Available slots.
- Capacity progress.
- Action edit/delete.

### 17.3. Capacity warning

Nếu:

```ts
assigned_count > total_slots
```

hiển thị cảnh báo đỏ.

Nếu gần đầy:

```ts
assigned_count / total_slots >= 0.9
```

hiển thị cảnh báo vàng.

---

## 18. Flight Allocation

### 18.1. Auto Allocation

Nút:

```text
Run Auto Flight Allocation
```

Confirmation modal phải giải thích:

- Ưu tiên giữ thành viên cùng Team.
- Cố gắng đáp ứng ca mong muốn.
- Không vượt slot chuyến bay.
- Các trường hợp ngoại lệ sẽ được flag.
- Team có thể bị tách nếu không đủ nguồn lực.

### 18.2. API

```text
POST /api/v1/admin/allocations/flights/auto
```

### 18.3. Result

Hiển thị:

- `success`
- `total_users`
- `allocated_users`
- `unallocated_users`
- `unallocated_user_ids`
- `warnings`
- `message`

### 18.4. Results table

Cột:

- User.
- Employee code.
- Team.
- Desired shift.
- Assigned flight.
- Allocation status.
- Warning/flag.

Filter:

- Chưa phân bổ.
- Team bị tách.
- Không đáp ứng ca.
- Theo flight.
- Theo Team.

### 18.5. Manual adjustment

API:

```text
PUT /api/v1/admin/allocations/flights/manual
```

Request:

```json
{
  "user_ids": ["uuid-1", "uuid-2"],
  "target_flight_id": "flight-uuid",
  "reason": "Điều chỉnh theo yêu cầu BTC"
}
```

UI cần:

- Chọn một hoặc nhiều user.
- Chọn flight đích.
- Nhập reason.
- Preview slot trước/sau.
- Hiển thị cảnh báo nếu vượt capacity.
- Backend là nguồn validate cuối cùng.

---

## 19. Vehicle Management

### 19.1. Vehicle form

Field:

- Event.
- Vehicle name.
- Route type.
- Departure time.
- Pickup location.
- Dropoff location.
- Capacity.
- Captain.
- Notes.

### 19.2. Vehicle table

Hiển thị:

- Vehicle name.
- Route.
- Departure.
- Pickup/dropoff.
- Capacity.
- Assigned count.
- Available capacity.
- Captain name.
- Captain phone.
- Notes.

### 19.3. Vehicle allocation

Chọn route:

```text
ROUTE_1
ROUTE_2
ROUTE_3
ROUTE_4
```

Chạy:

```text
POST /api/v1/admin/allocations/vehicles/auto
```

Hiển thị:

- Route type.
- Total users.
- Allocated users.
- Unallocated users.
- Unallocated user IDs.
- Message.

### 19.4. Manual vehicle adjustment

API:

```text
PUT /api/v1/admin/allocations/vehicles/manual
```

Request:

```json
{
  "user_ids": ["uuid-1"],
  "target_vehicle_id": "vehicle-uuid",
  "route_type": "ROUTE_1",
  "reason": "Điều chỉnh thủ công"
}
```

Trước khi submit:

- Preview capacity.
- Hiển thị số người hiện tại.
- Hiển thị số chỗ còn lại.
- Cảnh báo nếu vượt sức chứa.

---

## 20. Hotel Import

### 20.1. UI

Sử dụng drag-and-drop upload:

- `.xlsx`
- `.xls`
- `.csv`

Hiển thị:

- Tên file.
- Dung lượng.
- Trạng thái upload.
- Progress.
- Remove/replace file.
- Template download.

### 20.2. API

```text
POST /api/v1/admin/hotels/import-rooms
GET  /api/v1/admin/hotels/export-template
GET  /api/v1/admin/hotels
```

### 20.3. Kết quả import

Hiển thị:

- `total_rows`
- `successful_imports`
- `failed_imports`
- `errors`
- `message`

Nếu `failed_imports > 0`, không hiển thị là import hoàn toàn thành công.

### 20.4. Error handling

- Hiển thị lỗi từng dòng nếu backend trả về.
- Có thể cho download file lỗi nếu backend hỗ trợ.
- Không làm mất file người dùng đã chọn khi upload thất bại.
- Validate định dạng file trước khi gửi.

---

## 21. Gala Admin

### 21.1. Cấu hình Gala

Field:

- `is_enabled`
- `lock_duration_seconds`
- `turn_duration_seconds`

Backend validation:

```text
lock_duration_seconds: 30–3600
turn_duration_seconds: 30–3600
```

### 21.2. Quản lý ghế

Admin có thể:

- Tạo ghế.
- Sửa table code.
- Sửa seat position.
- Đổi status.
- Xem layout.
- Xem số available/locking/confirmed/unavailable.
- Quản lý Team turn.

### 21.3. Thao tác nguy hiểm

Khi reset hoặc disable Gala:

- Hiển thị confirmation.
- Nêu rõ ảnh hưởng đến Team đang thao tác.
- Không tự động reset nếu backend chưa xác nhận.

---

## 22. Notification và Email

### 22.1. Notification form

Field:

- Event.
- Title.
- Content.
- Notification type.
- Recipient scope nếu backend hỗ trợ.

Notification type:

```text
INFO
WARNING
URGENT
```

### 22.2. UI feedback

Sau khi tạo notification:

> Thông báo đã được tạo và hệ thống đã đưa tiến trình gửi email vào background. Việc email đến inbox còn phụ thuộc vào hệ thống email.

Không cam kết email đã đến ngay lập tức.

### 22.3. Các trigger

- Đăng ký thành công.
- BTC công bố thông tin.
- Thay đổi chuyến bay.
- Thay đổi xe.
- Thay đổi phòng.
- Thay đổi lịch trình.
- Thông báo khẩn.

---

## 23. Export dữ liệu

Khi download Excel/CSV:

- Dùng API client nhận response blob.
- Không dùng `window.open()` nếu API yêu cầu Authorization.
- Tên file nên chứa:
  - Tên loại dữ liệu.
  - Event.
  - Timestamp.

Ví dụ:

```text
registrations-team-building-2026-20260915.xlsx
```

Hiển thị loading trong lúc download.

---

## 24. Loading, Empty và Error States

### 24.1. Loading

Sử dụng:

- PageLoader cho lần tải đầu.
- Skeleton cho card/table.
- Button spinner cho mutation.
- Progress cho upload.

### 24.2. Empty

Ví dụ:

```text
Chưa có thông tin chuyến bay được công bố.
```

```text
Bạn chưa gửi đăng ký cho kỳ Team Building này.
```

```text
Chưa có notification mới.
```

### 24.3. Error

Error message nên thân thiện:

```text
Không thể tải dữ liệu. Vui lòng thử lại.
```

Có nút:

```text
Thử lại
```

Không hiển thị stack trace cho người dùng.

### 24.4. HTTP status mapping

| Status | Frontend behavior |
|---|---|
| `400` | Hiển thị lỗi nghiệp vụ |
| `401` | Refresh token hoặc chuyển Login |
| `403` | Access denied |
| `404` | Resource not found |
| `409` | Conflict, yêu cầu refetch |
| `422` | Map lỗi vào field |
| `500` | Thông báo hệ thống lỗi |

---

## 25. Accessibility

Frontend phải hỗ trợ:

- Semantic HTML.
- Label gắn đúng input.
- Keyboard navigation.
- Focus-visible.
- Modal focus trap.
- Escape để đóng modal.
- Focus quay lại trigger sau khi đóng modal.
- Contrast tối thiểu WCAG AA.
- Không chỉ dùng màu để biểu thị trạng thái.
- `aria-label` cho seat, icon button và action.
- `aria-live="polite"` cho toast/status.
- `role="alert"` cho lỗi quan trọng.
- Heading theo thứ tự.

Ví dụ seat aria label:

```text
Ghế A1, bàn TABLE_A, đang trống
Ghế A2, bàn TABLE_A, đã xác nhận
```

---

## 26. Security

- Không lưu password.
- Không log access token hoặc refresh token.
- Không render HTML notification trực tiếp nếu chưa sanitize.
- Không tin role chỉ từ localStorage.
- Không cho phép CBNV truy cập dữ liệu Admin bằng cách gọi API trực tiếp.
- Backend luôn phải kiểm tra quyền.
- API client phải xử lý 401 đúng cách.
- Không hard-code secret trong frontend.
- Không commit `.env` production.
- Không hiển thị dữ liệu nhạy cảm không cần thiết.
- Với production nên cân nhắc HttpOnly Secure cookie.

---

## 27. Testing

### 27.1. Unit test

Test:

- Date formatting.
- Enum labels.
- Permission helpers.
- Error normalization.
- Capacity calculation.
- Seat selection rules.
- Registration validation.

### 27.2. Component test

Test:

- Button loading/disabled.
- Modal.
- ConfirmDialog.
- Registration form.
- Shift selector.
- Vehicle route card.
- Journey timeline.
- Gala seat.
- Error state.
- Empty state.

### 27.3. Integration test

Các flow cần mock API:

1. Login thành công.
2. Login thất bại.
3. Access token hết hạn và refresh thành công.
4. Refresh thất bại.
5. Submit registration.
6. Update registration.
7. Registration closed.
8. Cancel vehicle.
9. Gala lock thành công.
10. Gala lock lỗi 409.
11. Gala confirm.
12. Hotel import lỗi một phần.
13. Auto allocation có user chưa phân bổ.

### 27.4. E2E test

Tối thiểu:

#### Flow 1: User journey

```text
Login
→ Journey
→ Xem thông tin event
→ Xem flight/vehicle/hotel/schedule
```

#### Flow 2: Registration

```text
Login
→ Registration
→ Chọn tham gia
→ Chọn ca
→ Chọn xe
→ Đồng ý điều khoản
→ Submit
→ Success
```

#### Flow 3: Registration closed

```text
Login
→ Registration
→ Form read-only
→ Không thể sửa
```

#### Flow 4: Admin allocation

```text
Login Admin
→ Dashboard
→ Flight allocation
→ Run auto allocation
→ Xem warning/unallocated
→ Manual adjustment
```

#### Flow 5: Gala

```text
Login Representative
→ Gala
→ Chọn seat
→ Lock
→ Confirm
→ Journey cập nhật
```

#### Flow 6: Mobile

Kiểm tra viewport:

```text
320px
375px
768px
1440px
```

Đảm bảo:

- Không overflow ngang ngoài chủ ý.
- Mobile menu hoạt động.
- Form dễ thao tác.
- Button đủ lớn.
- Table chuyển card hoặc scroll hợp lý.

---

## 28. Definition of Done

Một page chỉ được xem là hoàn thành khi:

- Có loading state.
- Có error state.
- Có empty state.
- Có success state.
- Responsive từ 320px đến desktop.
- Có keyboard navigation.
- Có focus state.
- Có aria cơ bản.
- Không gọi API trực tiếp trong JSX.
- Đã xử lý 401, 403, 409, 422.
- Có test happy path.
- Có test failure path.
- Không hard-code dữ liệu nghiệp vụ.
- TypeScript không có lỗi.
- Lint pass.
- Build production pass.
- Đã test mobile.

---

## 29. Các điểm cần chốt với Backend và Business

Trước khi implement chính thức cần xác nhận:

1. Endpoint chính thức cho `/events/active`.
2. Response pagination/filter/sort cho các admin list.
3. Endpoint lấy pickup/drop-off location.
4. `desired_shift` có bắt buộc khi `is_participating=false` hay không.
5. Điều kiện nào khiến CBNV được xem allocation.
6. Endpoint lấy Gala config và Gala turn cho user.
7. Notification list dành cho CBNV.
8. Notification read có persistence hay không.
9. Timezone chính thức của event.
10. Format import/export chính thức.
11. Production dùng SSO hay email/password.
12. `/auth/register` chỉ dùng cho Dev/Test hay production.
13. `/auth/bootstrap-admin` chỉ chạy khi setup hệ thống hay không.
14. Cơ chế publish thông tin.
15. Quy tắc khi Team không đủ slot flight.
16. Quy tắc khi hủy xe sau khi đã allocation.
17. Người đại diện Team được xác định như thế nào.
18. Số ghế Gala tối đa theo số thành viên hợp lệ.
19. Thời gian lock và thời gian mỗi lượt.
20. Có cần audit log frontend hay chỉ backend lưu.

---

## 30. Trình tự implement đề xuất

### Sprint 1: Frontend foundation

- Khởi tạo Vite.
- Cấu hình TypeScript.
- Cấu hình Tailwind.
- Tạo AppLayout/AuthLayout/AdminLayout.
- Tạo routing.
- Tạo Axios client.
- Tạo authentication.
- Tạo design system.
- Tạo các type chính.
- Tạo React Query provider.

### Sprint 2: Authentication và CBNV Registration

- Login.
- Refresh token.
- Logout.
- Protected route.
- User profile.
- Active event.
- Registration form.
- Submit/update.
- Cancel vehicle.
- Toast/error/confirmation.

### Sprint 3: My Journey

- Journey API.
- Journey header.
- Profile card.
- Registration status.
- Flight cards.
- Vehicle cards.
- Hotel card.
- Gala card.
- Timeline.
- Schedule.
- Notifications.

### Sprint 4: Admin Core

- Admin dashboard.
- Event management.
- Team management.
- User management.
- Flight management.
- Vehicle management.
- Search/filter/sort/pagination.

### Sprint 5: Allocation và Hotel

- Auto flight allocation.
- Manual flight adjustment.
- Flight result.
- Auto vehicle allocation.
- Manual vehicle adjustment.
- Capacity warning.
- Hotel import.
- Hotel template download.
- Import result.

### Sprint 6: Gala và Hardening

- Gala layout.
- Seat selection.
- Polling.
- Lock.
- Confirm.
- Release.
- Countdown.
- Conflict 409.
- Gala admin config.
- Accessibility.
- Testing.
- Docker/Nginx production build.

---

## 31. Checklist bàn giao Frontend

### Project setup

- [ ] React + TypeScript + Vite đã cấu hình.
- [ ] Tailwind CSS đã cấu hình.
- [ ] React Query đã cấu hình.
- [ ] Axios client đã cấu hình.
- [ ] `.env.example` đã tạo.
- [ ] Không commit secret.

### Authentication

- [ ] Login hoạt động.
- [ ] Access token hoạt động.
- [ ] Refresh token hoạt động.
- [ ] Logout hoạt động.
- [ ] 401 được xử lý.
- [ ] Protected route hoạt động.
- [ ] Admin route hoạt động.
- [ ] Representative route hoạt động.

### User

- [ ] Registration form hoàn chỉnh.
- [ ] Validation frontend.
- [ ] Submit registration.
- [ ] Update registration.
- [ ] Cancel vehicle.
- [ ] Form read-only khi registration đóng.
- [ ] Success/error feedback.
- [ ] Journey responsive.
- [ ] Notification hiển thị.
- [ ] Schedule hiển thị.

### Gala

- [ ] Seat map responsive.
- [ ] Legend đầy đủ.
- [ ] Seat status đúng.
- [ ] Polling mỗi 2–3 giây.
- [ ] Polling dừng khi tab hidden.
- [ ] Lock hoạt động.
- [ ] Confirm hoạt động.
- [ ] Release hoạt động.
- [ ] Countdown hoạt động.
- [ ] Xử lý 409.
- [ ] Không cho chọn quá số lượng thành viên.

### Admin

- [ ] Dashboard KPI.
- [ ] Event CRUD.
- [ ] Team CRUD.
- [ ] User list.
- [ ] Flight CRUD.
- [ ] Vehicle CRUD.
- [ ] Auto flight allocation.
- [ ] Manual flight adjustment.
- [ ] Auto vehicle allocation.
- [ ] Manual vehicle adjustment.
- [ ] Hotel import.
- [ ] Hotel template download.
- [ ] Gala configuration.
- [ ] Notification management.
- [ ] Export dữ liệu.
- [ ] Audit log nếu backend hỗ trợ.

### Quality

- [ ] `tsc --noEmit` pass.
- [ ] Lint pass.
- [ ] Unit test pass.
- [ ] Integration test pass.
- [ ] E2E test pass.
- [ ] Production build pass.
- [ ] Mobile viewport 320px pass.
- [ ] Mobile viewport 375px pass.
- [ ] Tablet viewport 768px pass.
- [ ] Desktop viewport 1440px pass.
- [ ] Không có overflow ngang ngoài chủ ý.
- [ ] Accessibility cơ bản đạt yêu cầu.

---

## 32. Kết luận

Frontend cần được xây dựng theo hướng:

```text
React + TypeScript
        ↓
React Router
        ↓
Layouts và Route Guards
        ↓
Pages
        ↓
Reusable Components
        ↓
React Query Hooks
        ↓
Axios API Client
        ↓
FastAPI Backend
```

Các nguyên tắc bắt buộc:

- Mobile-first.
- Responsive.
- Component hóa.
- Type-safe.
- Server state dùng React Query.
- API call tách khỏi UI.
- Backend là nguồn dữ liệu và phân quyền cuối cùng.
- Không hard-code dữ liệu nghiệp vụ.
- Xử lý đầy đủ loading, empty, error, conflict và read-only state.
- Gala Dinner phải xử lý polling và optimistic locking đúng quy trình.
- Mọi thông tin CBNV nhìn thấy phải lấy từ nguồn dữ liệu đã được backend công bố.

Khi bắt đầu code, cần lấy OpenAPI JSON của FastAPI làm nguồn contract cuối cùng. Nếu schema thực tế khác tài liệu này, ưu tiên schema/version backend đã phát hành và cập nhật lại TypeScript type trước khi xây UI.
