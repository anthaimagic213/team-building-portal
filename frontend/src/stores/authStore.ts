import {
  useSyncExternalStore,
} from 'react';

import type {
  AuthSession,
  AuthUser,
  UserRole,
} from '@/types/auth';

import {
  tokenStorage,
} from '@/api/httpClient';

const AUTH_SESSION_EVENT = 'team-building-auth-session-changed';

let currentSession: AuthSession | null = null;

const listeners = new Set<() => void>();

function notifyListeners(): void {
  listeners.forEach((listener) => {
    listener();
  });

  window.dispatchEvent(
    new CustomEvent(AUTH_SESSION_EVENT),
  );
}

function readStoredSession(): AuthSession | null {
  const accessToken = tokenStorage.getAccessToken();
  const refreshToken = tokenStorage.getRefreshToken();

  if (!accessToken || !refreshToken) {
    return null;
  }

  const rawUser = localStorage.getItem('auth_user');

  if (!rawUser) {
    return {
      accessToken,
      refreshToken,
      user: {
        id: '',
        empCode: '',
        fullName: '',
        roles: [],
      },
    };
  }

  try {
    const user = JSON.parse(rawUser) as AuthUser;

    return {
      accessToken,
      refreshToken,
      user,
    };
  } catch {
    localStorage.removeItem('auth_user');

    return {
      accessToken,
      refreshToken,
      user: {
        id: '',
        empCode: '',
        fullName: '',
        roles: [],
      },
    };
  }
}

function getSnapshot(): AuthSession | null {
  if (currentSession === null) {
    currentSession = readStoredSession();
  }

  return currentSession;
}

function getServerSnapshot(): AuthSession | null {
  return null;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);

  const handleExternalChange = () => {
    currentSession = readStoredSession();
    listener();
  };

  window.addEventListener(
    AUTH_SESSION_EVENT,
    handleExternalChange,
  );

  window.addEventListener(
    'storage',
    handleExternalChange,
  );

  return () => {
    listeners.delete(listener);

    window.removeEventListener(
      AUTH_SESSION_EVENT,
      handleExternalChange,
    );

    window.removeEventListener(
      'storage',
      handleExternalChange,
    );
  };
}

export const authStore = {
  getSession(): AuthSession | null {
    return getSnapshot();
  },

  setSession(session: AuthSession): void {
    currentSession = session;

    localStorage.setItem(
      'auth_user',
      JSON.stringify(session.user),
    );

    notifyListeners();
  },

  setUser(user: AuthUser): void {
    const session = getSnapshot();

    if (!session) {
      return;
    }

    authStore.setSession({
      ...session,
      user,
    });
  },

  setUserFromTokenResponse(data: {
    access_token: string;
    refresh_token: string;
    user_id: string;
    emp_code: string;
    full_name: string;
    roles: UserRole[];
  }): void {
    authStore.setSession({
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      user: {
        id: data.user_id,
        empCode: data.emp_code,
        fullName: data.full_name,
        roles: data.roles,
      },
    });
  },

  clearSession(): void {
    currentSession = null;

    tokenStorage.clear();
    localStorage.removeItem('auth_user');

    notifyListeners();
  },

  isAuthenticated(): boolean {
    return Boolean(
      tokenStorage.getAccessToken() &&
      tokenStorage.getRefreshToken(),
    );
  },

  hasRole(role: UserRole): boolean {
    const session = getSnapshot();

    return Boolean(
      session?.user.roles.includes(role),
    );
  },

  hasAnyRole(roles: UserRole[]): boolean {
    const session = getSnapshot();

    if (!session) {
      return false;
    }

    return roles.some((role) =>
      session.user.roles.includes(role),
    );
  },
};

export function useAuthStore(): AuthSession | null {
  return useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot,
  );
}

export function useAuthSnapshot(): AuthSession | null {
  return useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot,
  );
}

export default authStore;
