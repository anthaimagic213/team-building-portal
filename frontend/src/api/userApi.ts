import httpClient from './httpClient';
import type { UserRole } from './authApi';

export interface Team {
  id: string;
  event_id: string;
  team_name: string;
  member_count?: number;
}

export interface UserResponse {
  id: string;
  emp_code: string;
  full_name: string;
  email: string;
  phone?: string | null;
  team_id?: string | null;
  team_name?: string | null;
  is_representative: boolean;
  roles?: UserRole[];
}

export interface UserSelfUpdateRequest {
  phone?: string | null;
  password?: string;
}

export interface UserListItem {
  id: string;
  emp_code: string;
  full_name: string;
  email: string;
  phone?: string | null;
  team_id?: string | null;
  team_name?: string | null;
  is_representative: boolean;
  is_registered?: boolean;
  is_participating?: boolean;
  desired_shift?: string | null;
  has_flight?: boolean;
  has_vehicle?: boolean;
  has_hotel?: boolean;
}

export const userApi = {
  async listEventTeams(eventId: string): Promise<Team[]> {
    const response = await httpClient.get<Team[]>(`/users/events/${eventId}/teams`);
    return response.data;
  },
  async getMe(): Promise<UserResponse> {
    const response = await httpClient.get<UserResponse>('/users/me');
    return response.data;
  },

  async updateMe(
    payload: UserSelfUpdateRequest,
  ): Promise<UserResponse> {
    const response = await httpClient.put<UserResponse>(
      '/users/me',
      payload,
    );
    return response.data;
  },

};

export default userApi;
