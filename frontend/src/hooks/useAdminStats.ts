import {
  useQuery,
} from '@tanstack/react-query';

import {
  adminApi,
} from '@/api';

import type {
  AdminDashboardStats,
} from '@/types/admin';

import {
  queryKeys,
} from '@/constants/queryKeys';

import {
  authStore,
} from '@/stores/authStore';

export function useAdminStats(
  eventId?: string,
) {
  const hasAdminRole =
    authStore.hasAnyRole([
      'ADMIN',
      'SUPER_ADMIN',
    ]);

  return useQuery<AdminDashboardStats>({
    queryKey: queryKeys.adminStats(eventId),

    queryFn: async () => {
      const data = eventId
        ? await adminApi.getEventStatistics(eventId)
        : await adminApi.getDashboardStats();

      return data as AdminDashboardStats;
    },

    enabled:
      authStore.isAuthenticated() &&
      hasAdminRole,

    staleTime: 30 * 1000,

    retry: 1,
  });
}

export default useAdminStats;
