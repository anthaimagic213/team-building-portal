import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import {
  journeyApi,
} from '@/api';

import type {
  JourneySummary,
  MyJourneyResponse,
} from '@/types/journey';

import {
  queryKeys,
} from '@/constants/queryKeys';

import {
  authStore,
} from '@/stores/authStore';

export function useJourney(options: { enabled?: boolean } = {}) {
  const queryClient = useQueryClient();

  const journeyQuery = useQuery<MyJourneyResponse>({
    queryKey: queryKeys.journey,

    queryFn: () =>
      journeyApi.getMyJourney(),

    enabled: authStore.isAuthenticated() && options.enabled !== false,

    staleTime: 30 * 1000,

    retry: 1,
  });

  const summaryQuery = useQuery<JourneySummary>({
    queryKey: queryKeys.journeySummary,

    queryFn: () =>
      journeyApi.getSummary(),

    enabled: authStore.isAuthenticated() && options.enabled !== false,

    staleTime: 30 * 1000,

    retry: 1,
  });

  const markNotificationMutation =
    useMutation({
      mutationFn: (notificationId: string) =>
        journeyApi.markNotificationAsRead(
          notificationId,
        ),

      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: queryKeys.journey,
        });
      },
    });

  return {
    journey: journeyQuery.data ?? null,
    summary: summaryQuery.data ?? null,

    isLoading:
      journeyQuery.isLoading ||
      summaryQuery.isLoading,

    isFetching:
      journeyQuery.isFetching ||
      summaryQuery.isFetching,

    isError:
      journeyQuery.isError ||
      summaryQuery.isError,

    error:
      journeyQuery.error ||
      summaryQuery.error,

    refetch: async () => {
      await Promise.all([
        journeyQuery.refetch(),
        summaryQuery.refetch(),
      ]);
    },

    markNotificationAsRead:
      markNotificationMutation.mutateAsync,

    isMarkingNotificationAsRead:
      markNotificationMutation.isPending,
  };
}

export default useJourney;
