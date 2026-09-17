import type { UserRole } from './auth';

export interface Team {
  id: string;
  event_id: string;
  team_name: string;
  member_count?: number;
}

export interface TeamCreateRequest {
  event_id: string;
  team_name: string;
}

export interface TeamUpdateRequest {
  team_name?: string;
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

export interface UserUpdateRequest {
  full_name?: string | null;
  phone?: string | null;
  team_id?: string | null;
  is_representative?: boolean;
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
  team_name?: string | null;
  work_location?: string | null;
  is_representative?: boolean;
  is_registered?: boolean;
  is_participating?: boolean;
  desired_shift?: string | null;
  has_flight?: boolean;
  has_vehicle?: boolean;
  has_hotel?: boolean;
}
