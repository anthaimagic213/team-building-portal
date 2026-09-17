import {
  useCallback,
  useMemo,
} from 'react';

import {
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';

import {
  authApi,
} from '@/api';

import type {
  LoginRequest,
  TokenResponse,
  UserRole,
} from '@/types/auth';

import {
  authStore,
  useAuthSnapshot,
} from '@/stores/authStore';

export function useAuth() {
  const queryClient = useQueryClient();
  const session = useAuthSnapshot();

  const loginMutation = useMutation({
    mutationFn: (payload: LoginRequest) =>
      authApi.login(payload),

    onSuccess: (data: TokenResponse) => {
      authStore.setUserFromTokenResponse(data);

      queryClient.invalidateQueries({
        queryKey: ['users', 'me'],
      });
    },
  });

  const logoutMutation = useMutation({
    mutationFn: () => authApi.logout(),

    onSettled: () => {
      authStore.clearSession();
      queryClient.clear();
    },
  });

  const login = useCallback(
    async (payload: LoginRequest) => {
      const data = await loginMutation.mutateAsync(payload);

      authStore.setUserFromTokenResponse(data);

      return data;
    },
    [loginMutation],
  );

  const logout = useCallback(async () => {
    await logoutMutation.mutateAsync();
  }, [logoutMutation]);

  const hasRole = useCallback(
    (role: UserRole): boolean => {
      return Boolean(
        session?.user.roles.includes(role),
      );
    },
    [session],
  );

  const hasAnyRole = useCallback(
    (roles: UserRole[]): boolean => {
      if (!session) {
        return false;
      }

      return roles.some((role) =>
        session.user.roles.includes(role),
      );
    },
    [session],
  );

  const value = useMemo(
    () => ({
      session,
      user: session?.user ?? null,
      isAuthenticated: Boolean(session),
      isLoggingIn: loginMutation.isPending,
      isLoggingOut: logoutMutation.isPending,
      loginError: loginMutation.error,
      logoutError: logoutMutation.error,
      login,
      logout,
      hasRole,
      hasAnyRole,
    }),
    [
      session,
      loginMutation.isPending,
      loginMutation.error,
      logoutMutation.isPending,
      logoutMutation.error,
      login,
      logout,
      hasRole,
      hasAnyRole,
    ],
  );

  return value;
}

export default useAuth;
