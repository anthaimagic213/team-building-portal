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

  galaTurns: (eventId: string) =>
    ['admin', 'gala', 'turns', eventId] as const,

  adminStats: (eventId?: string) =>
    ['admin', 'dashboard', 'stats', eventId] as const,

  eventStatistics: (eventId: string) =>
    ['admin', 'dashboard', 'statistics', eventId] as const,

  teamStatistics: (eventId: string) =>
    ['admin', 'dashboard', 'teams', eventId] as const,

  adminUsers: (eventId?: string, params?: unknown) =>
    ['admin', 'users', eventId, params] as const,

  adminEvents: (params?: unknown) =>
    ['admin', 'events', params] as const,

  adminTeams: (params?: unknown) =>
    ['admin', 'teams', params] as const,

  adminFlights: (params?: unknown) =>
    ['admin', 'flights', params] as const,

  adminVehicles: (params?: unknown) =>
    ['admin', 'vehicles', params] as const,

  adminHotels: (eventId?: string) =>
    ['admin', 'hotels', eventId] as const,

  notifications: (eventId: string) =>
    ['admin', 'notifications', eventId] as const,

  flightAllocationResults: (params?: unknown) =>
    ['admin', 'allocations', 'flights', 'results', params] as const,

  flightAllocationStats: (eventId?: string) =>
    ['admin', 'allocations', 'flights', 'stats', eventId] as const,

  vehicleAllocationResults: (
    routeType: string,
    eventId?: string,
  ) =>
    [
      'admin',
      'allocations',
      'vehicles',
      'results',
      routeType,
      eventId,
    ] as const,
};

export default queryKeys;
