import {
  useQuery,
} from '@tanstack/react-query';

import {
  eventApi,
} from '@/api';

import type {
  EventResponse,
} from '@/types/event';

import {
  queryKeys,
} from '@/constants/queryKeys';

import {
  authStore,
} from '@/stores/authStore';

export function useActiveEvent() {
  return useQuery<EventResponse | null>({
    queryKey: queryKeys.activeEvent,

    queryFn: () => eventApi.getActiveEvent(),

    enabled: authStore.isAuthenticated(),

    staleTime: 60 * 1000,

    retry: 1,
  });
}

export default useActiveEvent;
