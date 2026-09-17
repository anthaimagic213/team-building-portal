import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import {
  registrationApi,
} from '@/api';

import type {
  CancelVehicleRequest,
  RegistrationCreateRequest,
  RegistrationResponse,
  RegistrationUpdateRequest,
} from '@/types/registration';

import {
  queryKeys,
} from '@/constants/queryKeys';

import {
  authStore,
} from '@/stores/authStore';

export function useRegistration(eventId?: string) {
  const queryClient = useQueryClient();

  const registrationQuery =
    useQuery<RegistrationResponse | null>({
      queryKey: [...queryKeys.registration, eventId],

      queryFn: () =>
        registrationApi.getMyRegistration(eventId),

      enabled: authStore.isAuthenticated(),

      staleTime: 30 * 1000,

      retry: 1,
    });

  const invalidateRegistrationQueries = async () => {
    await Promise.all([
      queryClient.invalidateQueries({
        queryKey: queryKeys.registration,
      }),

      queryClient.invalidateQueries({
        queryKey: queryKeys.journey,
      }),

      queryClient.invalidateQueries({
        queryKey: queryKeys.journeySummary,
      }),
    ]);
  };

  const submitMutation =
    useMutation<RegistrationResponse, unknown, RegistrationCreateRequest>({
      mutationFn: (payload) =>
        registrationApi.submitRegistration(payload),

      onSuccess: invalidateRegistrationQueries,
    });

  const updateMutation =
    useMutation<
      RegistrationResponse,
      unknown,
      RegistrationUpdateRequest
    >({
      mutationFn: (payload) =>
        registrationApi.updateRegistration(payload),

      onSuccess: invalidateRegistrationQueries,
    });

  const cancelVehicleMutation =
    useMutation<
      unknown,
      unknown,
      CancelVehicleRequest
    >({
      mutationFn: (payload) =>
        registrationApi.cancelVehicleRoute(payload),

      onSuccess: invalidateRegistrationQueries,
    });

  return {
    ...registrationQuery,

    registration: registrationQuery.data ?? null,

    submitRegistration: submitMutation.mutateAsync,
    updateRegistration: updateMutation.mutateAsync,
    cancelVehicleRoute: cancelVehicleMutation.mutateAsync,

    isSubmitting: submitMutation.isPending,
    isUpdating: updateMutation.isPending,
    isCancellingVehicle: cancelVehicleMutation.isPending,

    submitError: submitMutation.error,
    updateError: updateMutation.error,
    cancelVehicleError: cancelVehicleMutation.error,
  };
}

export default useRegistration;
