export const ROUTES = {
  login: '/login',
  journey: '/journey',
  registration: '/registration',
  gala: '/gala/:eventId',
  admin: '/admin',
  terms: '/terms',

  adminEvents: '/admin/events',
  adminTeams: '/admin/teams',
  adminUsers: '/admin/users',
  adminFlights: '/admin/flights',
  adminVehicles: '/admin/vehicles',
  adminFlightAllocation: '/admin/allocations/flights',
  adminVehicleAllocation: '/admin/allocations/vehicles',
  adminHotels: '/admin/hotels',
  adminGala: '/admin/gala',
  adminNotifications: '/admin/notifications',
} as const;

interface UserNavItem {
  to: string;
  label: string;
  representativeOnly?: boolean;
}

interface AdminNavItem {
  to: string;
  label: string;
}

export const USER_NAV_ITEMS: UserNavItem[] = [
  {
    to: ROUTES.journey,
    label: 'Hành trình của tôi',
  },
  {
    to: ROUTES.registration,
    label: 'Đăng ký Team Building',
  },
  {
    to: ROUTES.gala,
    label: 'Chọn ghế Gala',
    representativeOnly: true,
  },
];

export const ADMIN_NAV_ITEMS: AdminNavItem[] = [
  {
    to: ROUTES.admin,
    label: 'Tổng quan',
  },
  {
    to: ROUTES.adminEvents,
    label: 'Sự kiện',
  },
  {
    to: ROUTES.adminTeams,
    label: 'Team',
  },
  {
    to: ROUTES.adminUsers,
    label: 'CBNV',
  },
  {
    to: ROUTES.adminFlights,
    label: 'Chuyến bay',
  },
  {
    to: ROUTES.adminVehicles,
    label: 'Xe',
  },
  {
    to: ROUTES.adminFlightAllocation,
    label: 'Phân bổ chuyến bay',
  },
  {
    to: ROUTES.adminVehicleAllocation,
    label: 'Phân bổ xe',
  },
  {
    to: ROUTES.adminHotels,
    label: 'Khách sạn',
  },
  {
    to: ROUTES.adminGala,
    label: 'Gala Dinner',
  },
  {
    to: ROUTES.adminNotifications,
    label: 'Thông báo',
  },
];
