export { default as httpClient } from './httpClient';

export { default as authApi } from './authApi';
export { default as userApi } from './userApi';
export { default as eventApi } from './eventApi';
export { default as registrationApi } from './registrationApi';
export { default as journeyApi } from './journeyApi';
export type { JourneyEventItem } from './journeyApi';
export { default as galaApi } from './galaApi';
export { default as adminApi } from './adminApi';
export { default as allocationApi } from './allocationApi';
export { default as notificationApi } from './notificationApi';

export {
  tokenStorage,
  getApiErrorMessage,
  isConflictError,
  isValidationError,
} from './httpClient';

export type {
  UserRole,
  LoginRequest,
  TokenResponse,
  RefreshTokenRequest,
  RegisterRequest,
} from './authApi';

export type {
  Team,
  UserResponse,
  UserListItem,
} from './userApi';

export type {
  EventStatus,
  EventResponse,
  EventCreateRequest,
  EventUpdateRequest,
} from './eventApi';

export type {
  DesiredShift,
  RegistrationForm,
  RegistrationUpdateRequest,
  RegistrationResponse,
  CancelVehicleRequest,
} from './registrationApi';

export type {
  JourneyFlightInfo,
  JourneyVehicleInfo,
  JourneyHotelInfo,
  JourneyGalaInfo,
  EventScheduleItem,
  NotificationItem,
  MyJourneyResponse,
  JourneySummary,
} from './journeyApi';

export type {
  SeatStatus,
  GalaTurnStatus,
  GalaSeatResponse,
  GalaSeatingLayout,
  SeatLockRequest,
  SeatConfirmRequest,
  SeatReleaseRequest,
  GalaConfigResponse,
  GalaTeamTurnResponse,
} from './galaApi';

export type {
  FlightAllocationResult,
  ManualFlightAdjustmentRequest,
  VehicleAllocationResult,
  ManualVehicleAdjustmentRequest,
  AllocationResultListParams,
} from './allocationApi';

export type {
  FlightDirection,
  RouteType as AdminRouteType,
  FlightResponse,
  FlightCreateRequest,
  FlightUpdateRequest,
  VehicleResponse,
  VehicleCreateRequest,
  VehicleUpdateRequest,
  EventStatistics,
  TeamCreateRequest,
  TeamUpdateRequest,
  AdminListParams,
} from './adminApi';

export type {
  NotificationType,
  NotificationCreateRequest,
  NotificationResponse,
  NotificationListResponse,
} from './notificationApi';
