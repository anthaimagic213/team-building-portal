import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import {
  galaApi,
} from '@/api';

import type {
  GalaSeatingLayout,
} from '@/types/gala';

import {
  queryKeys,
} from '@/constants/queryKeys';

import {
  authStore,
} from '@/stores/authStore';

interface UseGalaSeatsOptions {
  enabled?: boolean;
  pollingInterval?: number;
}

export function useGalaSeats(
  eventId: string | undefined,
  options: UseGalaSeatsOptions = {},
) {
  const queryClient = useQueryClient();

  const enabled =
    Boolean(eventId) &&
    authStore.isAuthenticated() &&
    options.enabled !== false;

  const pollingInterval =
    options.pollingInterval ??
    Number(
      import.meta.env.VITE_GALA_POLLING_INTERVAL ||
      3000,
    );

  const seatsQuery = useQuery<GalaSeatingLayout>({
    queryKey: queryKeys.galaSeats(eventId ?? ''),

    queryFn: () => galaApi.getSeats(eventId ?? ''),

    enabled,

    staleTime: 0,

    refetchInterval: enabled
      ? pollingInterval
      : false,

    // Seat availability must stay live even when the browser tab is not focused.
    refetchIntervalInBackground: true,

    retry: 1,
  });

  const refetchSeats = async () => {
    await queryClient.invalidateQueries({
      queryKey: queryKeys.galaSeats(eventId ?? ''),
    });
  };

  const lockMutation = useMutation({
    mutationFn: (seatCodes: string[]) =>
      galaApi.lockSeats(eventId ?? '', seatCodes),

    onSuccess: refetchSeats,
  });

  const confirmMutation = useMutation({
    mutationFn: (seatCodes: string[]) =>
      galaApi.confirmSeats(eventId ?? '', seatCodes),

    onSuccess: async () => {
      await refetchSeats();

      await queryClient.invalidateQueries({
        queryKey: queryKeys.journey,
      });
    },
  });

  const releaseMutation = useMutation({
    mutationFn: (seatCodes: string[]) =>
      galaApi.releaseSeats(eventId ?? '', seatCodes),

    onSuccess: refetchSeats,
  });

  return {
    layout: seatsQuery.data ?? null,

    seats: seatsQuery.data?.seats ?? [],

    isLoading: seatsQuery.isLoading,
    isFetching: seatsQuery.isFetching,
    isError: seatsQuery.isError,
    error: seatsQuery.error,

    refetch: seatsQuery.refetch,

    lockSeats: lockMutation.mutateAsync,
    confirmSeats: confirmMutation.mutateAsync,
    releaseSeats: releaseMutation.mutateAsync,

    isLocking: lockMutation.isPending,
    isConfirming: confirmMutation.isPending,
    isReleasing: releaseMutation.isPending,

    lockError: lockMutation.error,
    confirmError: confirmMutation.error,
    releaseError: releaseMutation.error,
  };
}

export default useGalaSeats;
