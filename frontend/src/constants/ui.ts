export const APP_NAME = 'Team Building Portal';
export const MOBILE_BREAKPOINT = 768;
export const GALA_POLLING_INTERVAL = Number(import.meta.env.VITE_GALA_POLLING_INTERVAL || 3000);
export const MAX_COMMENT_LENGTH = 1000;
export const MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024;

export const VEHICLE_ROUTES = [
  { number: 1 as const, code: 'ROUTE_1', label: 'Văn phòng → Sân bay' },
  { number: 2 as const, code: 'ROUTE_2', label: 'Sân bay → Khách sạn' },
  { number: 3 as const, code: 'ROUTE_3', label: 'Khách sạn → Sân bay' },
  { number: 4 as const, code: 'ROUTE_4', label: 'Sân bay → Văn phòng' },
] as const;

export const EVENT_STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Bản nháp', REGISTRATION_OPEN: 'Đang mở đăng ký',
  REGISTRATION_CLOSED: 'Đã đóng đăng ký', ALLOCATION_IN_PROGRESS: 'Đang phân bổ',
  ALLOCATION_COMPLETED: 'Đã phân bổ', EVENT_ACTIVE: 'Đang diễn ra', EVENT_COMPLETED: 'Đã kết thúc',
};

export const ROUTE_LABELS: Record<string, string> = Object.fromEntries(
  VEHICLE_ROUTES.map((route) => [route.code, route.label]),
);
