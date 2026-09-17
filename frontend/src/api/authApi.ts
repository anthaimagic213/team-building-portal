import httpClient, { tokenStorage } from './httpClient';

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

export const authApi = {
  async login(payload: LoginRequest): Promise<TokenResponse> {
    const response = await httpClient.post<TokenResponse>(
      '/auth/login',
      payload,
    );

    tokenStorage.saveTokens(
      response.data.access_token,
      response.data.refresh_token,
    );

    return response.data;
  },

  async refresh(): Promise<TokenResponse> {
    const refreshToken = tokenStorage.getRefreshToken();

    if (!refreshToken) {
      throw new Error('Refresh token không tồn tại.');
    }

    const response = await httpClient.post<TokenResponse>(
      '/auth/refresh',
      {
        refresh_token: refreshToken,
      },
    );

    tokenStorage.saveTokens(
      response.data.access_token,
      response.data.refresh_token,
    );

    return response.data;
  },

  async logout(): Promise<void> {
    const refreshToken = tokenStorage.getRefreshToken();

    try {
      if (refreshToken) {
        await httpClient.post('/auth/logout', {
          refresh_token: refreshToken,
        });
      }
    } finally {
      tokenStorage.clear();
    }
  },

  async register(payload: RegisterRequest) {
    const response = await httpClient.post('/auth/register', payload);
    return response.data;
  },
};

export default authApi;
