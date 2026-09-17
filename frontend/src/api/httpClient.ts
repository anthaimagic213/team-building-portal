import axios, {
  AxiosError,
  AxiosInstance,
  InternalAxiosRequestConfig,
} from 'axios';



const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

type RetryableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: string;
  emp_code: string;
  full_name: string;
  roles: string[];
}

export const tokenStorage = {
  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  saveTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },

  clear(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

export const httpClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
});

let isRefreshing = false;

type PendingRequest = {
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
};

let pendingRequests: PendingRequest[] = [];

function resolvePendingRequests(error: unknown, token: string | null): void {
  pendingRequests.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else if (token) {
      resolve(token);
    }
  });

  pendingRequests = [];
}

function redirectToLogin(): void {
  tokenStorage.clear();

  if (window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
}

httpClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const accessToken = tokenStorage.getAccessToken();

    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => Promise.reject(error),
);

httpClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined;

    if (!originalRequest || error.response?.status !== 401) {
      return Promise.reject(error);
    }

    if (originalRequest.url?.includes('/auth/refresh')) {
      redirectToLogin();
      return Promise.reject(error);
    }

    if (originalRequest._retry) {
      redirectToLogin();
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingRequests.push({
          resolve: (token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(httpClient(originalRequest));
          },
          reject,
        });
      });
    }

    isRefreshing = true;

    const refreshToken = tokenStorage.getRefreshToken();

    if (!refreshToken) {
      isRefreshing = false;
      redirectToLogin();
      return Promise.reject(error);
    }

    try {
      const response = await axios.post<RefreshTokenResponse>(
        `${API_BASE_URL}/auth/refresh`,
        {
          refresh_token: refreshToken,
        },
      );

      const tokenData = response.data;

      tokenStorage.saveTokens(
        tokenData.access_token,
        tokenData.refresh_token,
      );

      resolvePendingRequests(null, tokenData.access_token);

      originalRequest.headers.Authorization = `Bearer ${tokenData.access_token}`;

      return httpClient(originalRequest);
    } catch (refreshError) {
      resolvePendingRequests(refreshError, null);
      redirectToLogin();

      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === 'string') {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail
        .map((item) => item?.msg || 'Dữ liệu không hợp lệ')
        .join(', ');
    }

    if (error.response?.status === 401) {
      return 'Phiên đăng nhập đã hết hạn.';
    }

    if (error.response?.status === 403) {
      return 'Bạn không có quyền thực hiện thao tác này.';
    }

    if (error.response?.status === 404) {
      return 'Không tìm thấy dữ liệu yêu cầu.';
    }

    if (error.response?.status === 409) {
      return 'Dữ liệu hiện tại đã thay đổi. Vui lòng tải lại trang.';
    }

    if (error.response?.status === 422) {
      return 'Dữ liệu gửi lên không hợp lệ.';
    }
  }

  return 'Có lỗi xảy ra. Vui lòng thử lại.';
}

export function isConflictError(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 409;
}

export function isValidationError(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 422;
}

export default httpClient;
