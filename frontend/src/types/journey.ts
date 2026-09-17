import type { EventStatus } from './event';

export interface JourneyFlightInfo {
  flight_code: string;
  direction: 'OUTBOUND' | 'RETURN';
  departure_time: string;
  arrival_time: string;
  origin: string;
  destination: string;
}


export interface JourneyVehicleInfo {
  vehicle_name: string;
  route_type:
    | 'ROUTE_1'
    | 'ROUTE_2'
    | 'ROUTE_3'
    | 'ROUTE_4';

  departure_time: string;
  pickup_location: string;
  dropoff_location?: string | null;
  captain_name?: string | null;
  captain_phone?: string | null;
  notes?: string | null;
}

export interface JourneyHotelInfo {
  hotel_name: string;
  address?: string | null;
  phone?: string | null;
  room_code: string;
  room_type?: string | null;
  roommates: string[];
}

export interface JourneyGalaInfo {
  seat_code: string;
  table_code?: string | null;
  seat_position?: number | null;
  status: string;
}

export interface EventScheduleItem {
  time: string;
  title: string;
  description?: string | null;
  location?: string | null;
}

export type NotificationType =
  | 'INFO'
  | 'WARNING'
  | 'URGENT'
  | string;

export interface NotificationItem {
  id: string;
  title: string;
  content: string;
  notification_type: NotificationType;
  created_at: string;
  is_read: boolean;
}

export interface MyJourneyResponse {
  user_name: string;
  emp_code: string;
  email: string;
  phone?: string | null;

  team_name?: string | null;
  team_leader?: string | null;

  event_name: string;
  event_date_start: string;
  event_date_end: string;
  event_location: string;
  event_status: EventStatus | string;

  is_participating: boolean;
  registration_status: string;

  outbound_flight?: JourneyFlightInfo | null;
  return_flight?: JourneyFlightInfo | null;

  vehicles: JourneyVehicleInfo[];

  hotel?: JourneyHotelInfo | null;

  gala_seat?: JourneyGalaInfo | null;

  schedule: EventScheduleItem[];
  notifications: NotificationItem[];

  last_updated: string;
}

export interface JourneySummary {
  user_name: string;
  emp_code: string;
  team_name?: string | null;

  has_flight: boolean;
  has_vehicle: boolean;
  has_hotel: boolean;
  has_gala_seat: boolean;

  completion_percentage: number;
}
