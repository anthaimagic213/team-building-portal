import httpClient from './httpClient';

export type DesiredShift = 'SHIFT_1' | 'SHIFT_2';

export interface RegistrationForm {
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

export interface CancelVehicleRequest {
  route_number: 1 | 2 | 3 | 4;
  reason?: string | null;
}

export const registrationApi = {
  async getMyRegistration(eventId?: string): Promise<RegistrationResponse | null> {
    const response = await httpClient.get<RegistrationResponse | null>(
      '/registrations/me',
      { params: eventId ? { event_id: eventId } : undefined },
    );

    return response.data;
  },

  async submitRegistration(
    payload: RegistrationForm,
  ): Promise<RegistrationResponse> {
    const response = await httpClient.post<RegistrationResponse>(
      '/registrations/submit',
      payload,
    );

    return response.data;
  },

  async updateRegistration(
    payload: RegistrationUpdateRequest,
  ): Promise<RegistrationResponse> {
    const response = await httpClient.put<RegistrationResponse>(
      '/registrations/update',
      payload,
    );

    return response.data;
  },

  async cancelVehicleRoute(
    payload: CancelVehicleRequest,
  ): Promise<unknown> {
    const response = await httpClient.post(
      '/registrations/cancel-vehicle',
      payload,
    );

    return response.data;
  },
};

export default registrationApi;
