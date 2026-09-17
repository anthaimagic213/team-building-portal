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

export interface GalaConfigCreateRequest {
  event_id: string;
  is_enabled: boolean;
  lock_duration_seconds: number;
  turn_duration_seconds: number;
  rows: number;
  columns: number;
}

export interface GalaConfigUpdateRequest {
  is_enabled?: boolean;
  lock_duration_seconds?: number;
  turn_duration_seconds?: number;
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

export interface GalaSeatCreateRequest {
  event_id: string;
  seat_code: string;
  table_code?: string | null;
  seat_position?: number | null;
  status?: SeatStatus;
}

export interface GalaSeatUpdateRequest {
  table_code?: string | null;
  seat_position?: number | null;
  status?: SeatStatus;
}

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

export interface SeatLockRequest {
  seat_codes: string[];
}

export interface SeatConfirmRequest {
  seat_codes: string[];
}

export interface SeatReleaseRequest {
  seat_codes: string[];
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
