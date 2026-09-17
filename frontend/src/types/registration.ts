export type DesiredShift = 'SHIFT_1' | 'SHIFT_2';

export type RegistrationStatus =
  | 'PENDING'
  | 'CONFIRMED'
  | 'CANCELLED'
  | string;

export interface RegistrationBase {
  event_id: string;
  team_id?: string | null;
  is_participating: boolean;
  desired_shift: DesiredShift | null;

  needs_vehicle_route_1: boolean;
  needs_vehicle_route_2: boolean;
  needs_vehicle_route_3: boolean;
  needs_vehicle_route_4: boolean;

  pickup_location_route_1?: string | null;
  pickup_location_route_4?: string | null;

  comments?: string | null;
}

export interface RegistrationCreateRequest
  extends RegistrationBase {
  agreed_to_terms: boolean;
}

export interface RegistrationUpdateRequest {
  event_id: string;
  team_id?: string | null;
  desired_shift?: DesiredShift | null;

  needs_vehicle_route_1?: boolean;
  needs_vehicle_route_2?: boolean;
  needs_vehicle_route_3?: boolean;
  needs_vehicle_route_4?: boolean;

  pickup_location_route_1?: string | null;
  pickup_location_route_4?: string | null;

  comments?: string | null;
}

export interface RegistrationResponse
  extends RegistrationBase {
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

  registration_status?: RegistrationStatus;
  agreed_to_terms?: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface CancelVehicleRequest {
  route_number: 1 | 2 | 3 | 4;
  reason?: string | null;
}

export interface RegistrationFormValues
  extends RegistrationCreateRequest {
  agreed_to_terms: boolean;
}
