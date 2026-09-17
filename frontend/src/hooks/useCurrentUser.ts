import {
  useQuery,
} from '@tanstack/react-query';

import {
  userApi,
} from '@/api';

import type {
  UserResponse,
} from '@/types/user';

import {
  queryKeys,
} from '@/constants/queryKeys';

import {
  authStore,
} from '@/stores/authStore';

export function useCurrentUser() {
  return useQuery<UserResponse>({
    queryKey: queryKeys.me,

    queryFn: () => userApi.getMe(),

    enabled: authStore.isAuthenticated(),

    staleTime: 5 * 60 * 1000,

    retry: 1,
  });
}

export default useCurrentUser;
