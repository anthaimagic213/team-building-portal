export type FlightDirection = 'OUTBOUND' | 'RETURN';

export type RouteType =
  | 'ROUTE_1'
  | 'ROUTE_2'
  | 'ROUTE_3'
  | 'ROUTE_4';

export interface FlightBase {
  flight_code: string;
  direction: FlightDirection;
  total_slots: number;
  departure_time: string;
  arrival_time: string;
  origin: string;
  destination: string;
}

export interface FlightCreateRequest extends FlightBase {
  event_id: string;
}

export interface FlightUpdateRequest {
  flight_code?: string;
  direction?: FlightDirection;
  total_slots?: number;
  departure_time?: string;
  arrival_time?: string;
  origin?: string;
  destination?: string;
}

export interface FlightResponse extends FlightBase {
  id: string;
  event_id: string;
  assigned_count: number;
  available_slots: number;
}

export interface VehicleBase {
  vehicle_name: string;
  route_type: RouteType;
  departure_time: string;
  pickup_location: string;
  dropoff_location?: string | null;
  capacity: number;
  captain_id?: string | null;
  notes?: string | null;
}

export interface VehicleCreateRequest extends VehicleBase {
  event_id: string;
}

export interface VehicleUpdateRequest {
  vehicle_name?: string;
  route_type?: RouteType;
  departure_time?: string;
  pickup_location?: string;
  dropoff_location?: string | null;
  capacity?: number;
  captain_id?: string | null;
  notes?: string | null;
}

export interface VehicleResponse extends VehicleBase {
  id: string;
  event_id: string;
  captain_name?: string | null;
  captain_phone?: string | null;
  assigned_count: number;
  available_capacity: number;
}
