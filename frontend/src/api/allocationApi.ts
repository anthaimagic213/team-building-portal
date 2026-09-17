import httpClient from './httpClient';

export type RouteType =
  | 'ROUTE_1'
  | 'ROUTE_2'
  | 'ROUTE_3'
  | 'ROUTE_4';

export interface FlightAllocationResult {
  success: boolean;
  total_users: number;
  allocated_users: number;
  unallocated_users: number;
  unallocated_user_ids: string[];
  warnings: string[];
  message: string;
}

export interface ManualFlightAdjustmentRequest {
  user_ids: string[];
  target_flight_id: string;
  reason?: string | null;
}

export interface VehicleAllocationResult {
  success: boolean;
  route_type: RouteType | string;
  total_users: number;
  allocated_users: number;
  unallocated_users: number;
  unallocated_user_ids: string[];
  message: string;
}

export interface ManualVehicleAdjustmentRequest {
  user_ids: string[];
  target_vehicle_id: string;
  route_type: RouteType;
  reason?: string | null;
}

export interface AllocationResultListParams {
  event_id?: string;
  route_type?: RouteType;
  page?: number;
  page_size?: number;
  search?: string;
}
export type FlightDirection = 'OUTBOUND' | 'RETURN';

export const allocationApi = {
  async runAutoFlightAllocation(
    eventId?: string,
    direction: FlightDirection = 'OUTBOUND',
    clearExisting = false,
  ): Promise<FlightAllocationResult> {
    const response = await httpClient.post<FlightAllocationResult>(
      '/admin/allocations/flights/auto',
      undefined,
      {
          params: { ...(eventId ? { event_id: eventId } : {}), direction, clear_existing: clearExisting },
      },
    );

    return response.data;
  },

  async clearFlightAllocations(
    eventId?: string,
    direction: FlightDirection = 'OUTBOUND',
  ): Promise<unknown> {
    const response = await httpClient.delete(
      '/admin/allocations/flights/clear',
      {
        params: { ...(eventId ? { event_id: eventId } : {}), direction },
      },
    );

    return response.data;
  },

  async manuallyAdjustFlight(
    payload: ManualFlightAdjustmentRequest,
  ): Promise<unknown> {
    const response = await httpClient.put(
      '/admin/allocations/flights/manual',
      payload,
    );

    return response.data;
  },

  async getFlightAllocationResults(
    params?: AllocationResultListParams,
  ): Promise<unknown> {
    const response = await httpClient.get(
      '/admin/allocations/flights/results',
      { params },
    );

    return response.data;
  },

  async getFlightAllocationStats(
    eventId?: string,
  ): Promise<unknown> {
    const response = await httpClient.get(
      '/admin/allocations/flights/stats',
      {
        params: eventId ? { event_id: eventId } : undefined,
      },
    );

    return response.data;
  },

  async runAutoVehicleAllocation(
    routeType: RouteType,
    eventId?: string,
    clearExisting = false,
  ): Promise<VehicleAllocationResult> {
    const response = await httpClient.post<VehicleAllocationResult>(
      '/admin/allocations/vehicles/auto',
      undefined,
      {
        params: {
          route_type: routeType,
          ...(eventId ? { event_id: eventId } : {}),
          clear_existing: clearExisting,
        },
      },
    );

    return response.data;
  },

  async clearVehicleAllocations(
    routeType?: RouteType,
    eventId?: string,
  ): Promise<unknown> {
    const response = await httpClient.delete(
      '/admin/allocations/vehicles/clear',
      {
        params: {
          ...(routeType ? { route_type: routeType } : {}),
          ...(eventId ? { event_id: eventId } : {}),
        },
      },
    );

    return response.data;
  },

  async manuallyAdjustVehicle(
    payload: ManualVehicleAdjustmentRequest,
  ): Promise<unknown> {
    const response = await httpClient.put(
      '/admin/allocations/vehicles/manual',
      payload,
    );

    return response.data;
  },

  async getVehicleAllocationResults(
    routeType: RouteType,
    eventId?: string,
  ): Promise<unknown> {
    const response = await httpClient.get(
      '/admin/allocations/vehicles/results',
      {
        params: {
          route_type: routeType,
          ...(eventId ? { event_id: eventId } : {}),
        },
      },
    );

    return response.data;
  },
};

export default allocationApi;
