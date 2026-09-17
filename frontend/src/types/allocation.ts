import type { RouteType } from './resource';

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

export interface HotelImportResult {
  success: boolean;
  total_rows: number;
  successful_imports: number;
  failed_imports: number;
  errors: string[];
  message: string;
}

export interface FlightAllocationResultItem {
  user_id: string;
  user_name?: string | null;
  emp_code?: string | null;
  team_id?: string | null;
  team_name?: string | null;
  desired_shift?: string | null;
  assigned_flight_id?: string | null;
  assigned_flight_code?: string | null;
  warnings?: string[];
}

export interface VehicleAllocationResultItem {
  user_id: string;
  user_name?: string | null;
  emp_code?: string | null;
  team_id?: string | null;
  team_name?: string | null;
  route_type: RouteType;
  assigned_vehicle_id?: string | null;
  vehicle_name?: string | null;
  warnings?: string[];
}

export interface AllocationListParams {
  event_id?: string;
  route_type?: RouteType;
  page?: number;
  page_size?: number;
  skip?: number;
  limit?: number;
  search?: string;
}
