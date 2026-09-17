import httpClient from './httpClient';
import type {
  EventResponse,
  EventCreateRequest,
  EventUpdateRequest,
} from './eventApi';
import type { Team, UserListItem } from './userApi';

export type FlightDirection = 'OUTBOUND' | 'RETURN';

export type RouteType =
  | 'ROUTE_1'
  | 'ROUTE_2'
  | 'ROUTE_3'
  | 'ROUTE_4';

export interface FlightResponse {
  id: string;
  event_id: string;
  flight_code: string;
  direction: FlightDirection;
  total_slots: number;
  departure_time: string;
  arrival_time: string;
  origin: string;
  destination: string;
  assigned_count: number;
  available_slots: number;
}

export interface FlightCreateRequest {
  event_id: string;
  flight_code: string;
  direction: FlightDirection;
  total_slots: number;
  departure_time: string;
  arrival_time: string;
  origin: string;
  destination: string;
}

export interface FlightUpdateRequest {
  flight_code?: string;
  direction?: FlightDirection;
  total_slots?: number;
  departure_time?: string;
  arrival_time?: string;
  origin?: string;
  destination?: string;
}

export interface VehicleResponse {
  id: string;
  event_id: string;
  vehicle_name: string;
  route_type: RouteType;
  departure_time: string;
  pickup_location: string;
  dropoff_location?: string | null;
  capacity: number;
  captain_id?: string | null;
  captain_name?: string | null;
  captain_phone?: string | null;
  notes?: string | null;
  assigned_count: number;
  available_capacity: number;
}

export interface VehicleCreateRequest {
  event_id: string;
  vehicle_name: string;
  route_type: RouteType;
  departure_time: string;
  pickup_location: string;
  dropoff_location?: string | null;
  capacity: number;
  captain_id?: string | null;
  notes?: string | null;
}

export interface VehicleUpdateRequest {
  vehicle_name?: string;
  route_type?: RouteType;
  departure_time?: string;
  pickup_location?: string;
  dropoff_location?: string | null;
  capacity?: number;
  captain_id?: string | null;
  notes?: string | null;
}

export interface EventStatistics {
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
  [key: string]: unknown;
}

export interface TeamCreateRequest {
  event_id: string;
  team_name: string;
}

export interface TeamUpdateRequest {
  team_name?: string;
}

export interface AdminListParams {
  event_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
  skip?: number;
  limit?: number;
}

export const adminApi = {
  async listEvents(
    params?: AdminListParams,
  ): Promise<EventResponse[]> {
    const response = await httpClient.get<EventResponse[]>(
      '/admin/events',
      { params },
    );

    return response.data;
  },

  async createEvent(
    payload: EventCreateRequest,
  ): Promise<EventResponse> {
    const response = await httpClient.post<EventResponse>(
      '/admin/events',
      payload,
    );

    return response.data;
  },

  async updateEvent(
    eventId: string,
    payload: EventUpdateRequest,
  ): Promise<EventResponse> {
    const response = await httpClient.put<EventResponse>(
      `/admin/events/${eventId}`,
      payload,
    );

    return response.data;
  },

  async deleteEvent(eventId: string): Promise<void> {
    await httpClient.delete(`/admin/events/${eventId}`);
  },

  async listTeams(
    params?: AdminListParams,
  ): Promise<Team[]> {
    const response = await httpClient.get<Team[]>(
      '/admin/teams',
      { params },
    );

    return response.data;
  },

  async createTeam(
    payload: TeamCreateRequest,
  ): Promise<Team> {
    const response = await httpClient.post<Team>(
      '/admin/teams',
      payload,
    );

    return response.data;
  },

  async updateTeam(
    teamId: string,
    payload: TeamUpdateRequest,
  ): Promise<Team> {
    const response = await httpClient.put<Team>(
      `/admin/teams/${teamId}`,
      payload,
    );

    return response.data;
  },

  async deleteTeam(teamId: string): Promise<void> {
    await httpClient.delete(`/admin/teams/${teamId}`);
  },

  async listUsers(
    eventId?: string,
    params?: Omit<AdminListParams, 'event_id'> & {
      team_id?: string;
      work_location?: string;
      has_registered?: boolean;
    },
  ): Promise<UserListItem[]> {
    if (!eventId) {
      return [];
    }

    const response = await httpClient.get<UserListItem[]>(
      `/admin/dashboard/users/${eventId}`,
      { params },
    );

    return response.data;
  },

  async listAllUsers(eventId?: string): Promise<UserListItem[]> {
    const response = await httpClient.get<UserListItem[]>('/admin/users', {
      params: eventId ? { event_id: eventId } : undefined,
    });
    return response.data;
  },

  async updateUserRepresentative(
    userId: string,
    eventId: string,
    isRepresentative: boolean,
  ): Promise<UserListItem> {
    const response = await httpClient.put<UserListItem>(
      `/admin/users/${userId}/representative`,
      { event_id: eventId, is_representative: isRepresentative },
    );
    return response.data;
  },

  async listFlights(
    params?: AdminListParams,
  ): Promise<FlightResponse[]> {
    const response = await httpClient.get<FlightResponse[]>(
      '/admin/resources/flights',
      { params },
    );

    return response.data;
  },

  async importFlights(file: File, eventId: string): Promise<unknown> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await httpClient.post('/admin/resources/flights/import', formData, {
      params: { event_id: eventId },
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async downloadFlightTemplate(): Promise<Blob> {
    const response = await httpClient.get('/admin/resources/flights/export-template', { responseType: 'blob' });
    return response.data;
  },

  async createFlight(
    payload: FlightCreateRequest,
  ): Promise<FlightResponse> {
    const response = await httpClient.post<FlightResponse>(
      '/admin/resources/flights',
      payload,
    );

    return response.data;
  },

  async updateFlight(
    flightId: string,
    payload: FlightUpdateRequest,
  ): Promise<FlightResponse> {
    const response = await httpClient.put<FlightResponse>(
      `/admin/resources/flights/${flightId}`,
      payload,
    );

    return response.data;
  },

  async deleteFlight(flightId: string): Promise<void> {
    await httpClient.delete(
      `/admin/resources/flights/${flightId}`,
    );
  },

  async listVehicles(
    params?: AdminListParams & { route_type?: RouteType },
  ): Promise<VehicleResponse[]> {
    const response = await httpClient.get<VehicleResponse[]>(
      '/admin/vehicles',
      { params },
    );

    return response.data;
  },

  async createVehicle(
    payload: VehicleCreateRequest,
  ): Promise<VehicleResponse> {
    const response = await httpClient.post<VehicleResponse>(
      '/admin/vehicles',
      payload,
    );

    return response.data;
  },

  async updateVehicle(
    vehicleId: string,
    payload: VehicleUpdateRequest,
  ): Promise<VehicleResponse> {
    const response = await httpClient.put<VehicleResponse>(
      `/admin/vehicles/${vehicleId}`,
      payload,
    );

    return response.data;
  },

  async deleteVehicle(vehicleId: string): Promise<void> {
    await httpClient.delete(
      `/admin/vehicles/${vehicleId}`,
    );
  },

  async getDashboardStats(
    eventId?: string,
  ): Promise<EventStatistics> {
    const response = await httpClient.get<EventStatistics>(
      '/admin/dashboard/stats',
      {
        params: eventId ? { event_id: eventId } : undefined,
      },
    );

    return response.data;
  },

  async getEventStatistics(
    eventId: string,
  ): Promise<EventStatistics> {
    const response = await httpClient.get<EventStatistics>(
      `/admin/dashboard/statistics/${eventId}`,
    );

    return response.data;
  },

  async getTeamStatistics(
    eventId: string,
  ): Promise<unknown[]> {
    const response = await httpClient.get<unknown[]>(
      `/admin/dashboard/teams/${eventId}`,
    );

    return response.data;
  },

  async importHotelRooms(file: File, eventId: string): Promise<unknown> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await httpClient.post(
      '/admin/hotels/import-rooms',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        params: { event_id: eventId },
      },
    );

    return response.data;
  },

  async getHotelList(
    eventId?: string,
  ): Promise<unknown[]> {
    const response = await httpClient.get<unknown[]>(
      '/admin/hotels',
      {
        params: eventId ? { event_id: eventId } : undefined,
      },
    );

    return response.data;
  },

  async downloadHotelTemplate(): Promise<Blob> {
    const response = await httpClient.get(
      '/admin/hotels/export-template',
      {
        responseType: 'blob',
      },
    );

    return response.data;
  },

  async exportRegistrations(
    params?: { event_id?: string; format?: 'xlsx' | 'csv' },
  ): Promise<Blob> {
    const response = await httpClient.get(
      '/admin/export/registrations',
      {
        params,
        responseType: 'blob',
      },
    );

    return response.data;
  },
};

export default adminApi;
