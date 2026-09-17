import type {
  EventResponse,
  EventStatus,
} from './event';

import type {
  Team,
  TeamCreateRequest,
  TeamUpdateRequest,
  UserListItem,
} from './user';

import type {
  FlightDirection,
  FlightResponse,
  FlightCreateRequest,
  FlightUpdateRequest,
  RouteType,
  VehicleResponse,
  VehicleCreateRequest,
  VehicleUpdateRequest,
} from './resource';

export interface AdminListParams {
  event_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
  skip?: number;
  limit?: number;
  status?: EventStatus;
  route_type?: RouteType;
}

export interface AdminDashboardStats {
  total_employees?: number;
  total_registered?: number;
  total_participating?: number;
  registration_rate?: number;
  total_flights?: number;
  allocated_flight_slots?: number;
  unallocated_flight_users?: number;
  unallocated_flight_user_ids?: string[];
  allocation_warnings?: string[];
  confirmed_gala_seats?: number;
  total_hotel_rooms_assigned?: number;
  total_users?: number;
  registered_users?: number;
  unregistered_users?: number;
  participating_users?: number;
  non_participating_users?: number;

  shift_1_count?: number;
  shift_2_count?: number;

  vehicle_route_1_count?: number;
  vehicle_route_2_count?: number;
  vehicle_route_3_count?: number;
  vehicle_route_4_count?: number;

  total_flight_slots?: number;
  used_flight_slots?: number;
  available_flight_slots?: number;

  total_vehicle_capacity?: number;
  used_vehicle_capacity?: number;
  available_vehicle_capacity?: number;

  [key: string]: unknown;
}

export interface AdminEventListResponse {
  items: EventResponse[];
  total: number;
  page?: number;
  page_size?: number;
}

export interface AdminTeamListResponse {
  items: Team[];
  total: number;
  page?: number;
  page_size?: number;
}

export interface AdminUserListResponse {
  items: UserListItem[];
  total: number;
  page?: number;
  page_size?: number;
}

export interface AdminFlightListResponse {
  items: FlightResponse[];
  total: number;
  page?: number;
  page_size?: number;
}

export interface AdminVehicleListResponse {
  items: VehicleResponse[];
  total: number;
  page?: number;
  page_size?: number;
}

export interface AdminResourceFilter {
  event_id?: string;
  search?: string;
  route_type?: RouteType;
  direction?: FlightDirection;
  page?: number;
  page_size?: number;
}

export interface AdminCrudTypes {
  event: EventResponse;
  team: Team;
  user: UserListItem;
  flight: FlightResponse;
  vehicle: VehicleResponse;
}

export type {
  EventResponse,
  EventStatus,
  Team,
  TeamCreateRequest,
  TeamUpdateRequest,
  UserListItem,
  FlightDirection,
  FlightResponse,
  FlightCreateRequest,
  FlightUpdateRequest,
  RouteType,
  VehicleResponse,
  VehicleCreateRequest,
  VehicleUpdateRequest,
};
