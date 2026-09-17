import httpClient from './httpClient';
import type {
  GalaConfigCreateRequest,
} from '@/types/gala';

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

export interface SeatLockRequest {
  seat_codes: string[];
}

export interface SeatConfirmRequest {
  seat_codes: string[];
}

export interface SeatReleaseRequest {
  seat_codes: string[];
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
  rows: number;
  columns: number;
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

function normalizeSeatCodes(seatCodes: string[]): string[] {
  return [...new Set(
    seatCodes
      .map((seatCode) => seatCode.trim().toUpperCase())
      .filter(Boolean),
  )];
}

export const galaApi = {
  async createAdminConfig(payload: GalaConfigCreateRequest): Promise<GalaConfigResponse> {
    const response = await httpClient.post<GalaConfigResponse>('/admin/gala/config', payload);
    return response.data;
  },
  async generateLayout(eventId: string, rows: number, columns: number): Promise<GalaConfigResponse> {
    const response = await httpClient.post<GalaConfigResponse>(`/admin/gala/layout/${eventId}`, null, { params: { rows, columns } });
    return response.data;
  },
  async getSeats(eventId: string): Promise<GalaSeatingLayout> {
    const response = await httpClient.get<GalaSeatingLayout>(`/gala/${eventId}/seats`);
    return response.data;
  },
  async updateSeat(seatId: string, status: SeatStatus): Promise<GalaSeatResponse> {
    const response = await httpClient.put<GalaSeatResponse>(`/admin/gala/seats/${seatId}`, { status });
    return response.data;
  },
  async lockSeats(eventId: string,
    seatCodes: string[],
  ): Promise<unknown> {
    const response = await httpClient.post(
      `/gala/${eventId}/lock`,
      {
        seat_codes: normalizeSeatCodes(seatCodes),
      },
    );

    return response.data;
  },

  async confirmSeats(eventId: string,
    seatCodes: string[],
  ): Promise<unknown> {
    const response = await httpClient.post(
      `/gala/${eventId}/confirm`,
      {
        seat_codes: normalizeSeatCodes(seatCodes),
      },
    );

    return response.data;
  },

  async releaseSeats(eventId: string,
    seatCodes: string[],
  ): Promise<unknown> {
    const response = await httpClient.post(
      `/gala/${eventId}/release`,
      {
        seat_codes: normalizeSeatCodes(seatCodes),
      },
    );

    return response.data;
  },

  async getAdminConfig(
    eventId: string,
  ): Promise<GalaConfigResponse> {
    const response = await httpClient.get<GalaConfigResponse>(
      `/admin/gala/config/${eventId}`,
    );

    return response.data;
  },

  async getTeamTurns(
    eventId: string,
  ): Promise<GalaTeamTurnResponse[]> {
    const response = await httpClient.get<GalaTeamTurnResponse[]>(
      `/admin/gala/turns/${eventId}`,
    );

    return response.data;
  },
  async randomizeTeamTurns(eventId: string): Promise<GalaTeamTurnResponse[]> {
    const response = await httpClient.post<GalaTeamTurnResponse[]>(`/admin/gala/turns/randomize/${eventId}`);
    return response.data;
  },
  async activateNextTurn(eventId: string): Promise<GalaTeamTurnResponse> {
    const response = await httpClient.post<GalaTeamTurnResponse>(`/admin/gala/turns/next/${eventId}`);
    return response.data;
  },
};

export default galaApi;
