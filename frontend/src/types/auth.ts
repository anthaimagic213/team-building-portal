export type UserRole =
  | 'USER'
  | 'ADMIN'
  | 'SUPER_ADMIN'
  | 'TEAM_REPRESENTATIVE';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: string;
  emp_code: string;
  full_name: string;
  roles: UserRole[];
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RegisterRequest {
  emp_code: string;
  full_name: string;
  email: string;
  password: string;
  phone?: string | null;
  team_id?: string | null;
  is_representative?: boolean;
}

export interface JwtPayload {
  sub: string;
  emp_code: string;
  team_id?: string | null;
  active_event_id?: string | null;
  roles: UserRole[];
  exp: number;
  type: 'access' | 'refresh';
}

export interface AuthSession {
  accessToken: string;
  refreshToken: string;
  user: AuthUser;
}

export interface AuthUser {
  id: string;
  empCode: string;
  fullName: string;
  roles: UserRole[];
}
