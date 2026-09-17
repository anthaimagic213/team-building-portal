import httpClient from './httpClient';
import type { EventStatus } from './eventApi';

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
  route_type: 'ROUTE_1' | 'ROUTE_2' | 'ROUTE_3' | 'ROUTE_4';
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

export interface NotificationItem {
  id: string;
  title: string;
  content: string;
  notification_type: 'INFO' | 'WARNING' | 'URGENT' | string;
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

export const journeyApi = {
  async listEvents(): Promise<JourneyEventItem[]> {
    const response = await httpClient.get<JourneyEventItem[]>('/journey/events');
    return response.data;
  },
  async getMyJourney(eventId?: string): Promise<MyJourneyResponse> {
    const response = await httpClient.get<MyJourneyResponse>('/journey/me', { params: eventId ? { event_id: eventId } : undefined });
    return response.data;
  },

  async getSummary(eventId?: string): Promise<JourneySummary> {
    const response = await httpClient.get<JourneySummary>('/journey/summary', { params: eventId ? { event_id: eventId } : undefined });

    return response.data;
  },

  async markNotificationAsRead(
    notificationId: string,
  ): Promise<unknown> {
    const response = await httpClient.post(
      `/journey/notifications/${notificationId}/read`,
    );

    return response.data;
  },
};

export interface JourneyEventItem {
  id: string;
  event_name: string;
  event_date_start: string;
  event_date_end: string;
  location: string;
  registration_deadline: string;
  status: string;
  teams: Array<{ id: string; team_name: string }>;
  participant_count: number;
  can_manage_gala: boolean;
  registration?: {
    id: string;
    team_id?: string | null;
    is_participating: boolean;
    assigned_flight_id?: string | null;
    assigned_outbound_flight_id?: string | null;
    assigned_return_flight_id?: string | null;
    assigned_vehicle_1_id?: string | null;
    assigned_vehicle_2_id?: string | null;
    assigned_vehicle_3_id?: string | null;
    assigned_vehicle_4_id?: string | null;
    hotel_room_code?: string | null;
    outbound_flight?: { flight_code: string; departure_time: string; arrival_time: string; origin: string; destination: string } | null;
    return_flight?: { flight_code: string; departure_time: string; arrival_time: string; origin: string; destination: string } | null;
    vehicles?: Array<{ route_type: string; vehicle_name: string; departure_time: string; pickup_location: string; dropoff_location?: string | null }>;
    hotel?: { hotel_name: string; room_code: string; room_type?: string | null } | null;
    gala_seat?: { seat_code: string; table_code?: string | null; seat_position?: number | null; status: string } | null;
  } | null;
}

export default journeyApi;
