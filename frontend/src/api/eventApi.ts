import httpClient from './httpClient';

export type EventStatus =
  | 'DRAFT'
  | 'REGISTRATION_OPEN'
  | 'REGISTRATION_CLOSED'
  | 'ALLOCATION_IN_PROGRESS'
  | 'ALLOCATION_COMPLETED'
  | 'EVENT_ACTIVE'
  | 'EVENT_COMPLETED';

export interface EventResponse {
  id: string;
  event_name: string;
  event_date_start: string;
  event_date_end: string;
  location: string;
  registration_deadline: string;
  description?: string | null;
  status: EventStatus;
  total_participants: number;
  created_at: string;
}

export interface EventCreateRequest {
  event_name: string;
  event_date_start: string;
  event_date_end: string;
  location: string;
  registration_deadline: string;
  description?: string | null;
}

export interface EventUpdateRequest {
  event_name?: string;
  event_date_start?: string;
  event_date_end?: string;
  location?: string;
  registration_deadline?: string;
  description?: string | null;
  status?: EventStatus;
}

export const eventApi = {
  async getActiveEvent(): Promise<EventResponse | null> {
    const response = await httpClient.get<EventResponse | null>('/admin/events/active');
    return response.data;
  },

  async listEvents(params?: {
    status?: EventStatus;
  }): Promise<EventResponse[]> {
    const response = await httpClient.get<EventResponse[]>('/admin/events', {
      params,
    });

    return response.data;
  },

  async getEvent(eventId: string): Promise<EventResponse> {
    const response = await httpClient.get<EventResponse>(
      `/admin/events/${eventId}`,
    );

    return response.data;
  },

  async createEvent(
    payload: EventCreateRequest,
  ): Promise<EventResponse> {
    const response = await httpClient.post<EventResponse>(
      '/admin/events',
      payload,
    );

    return response.data;
  },

  async updateEvent(
    eventId: string,
    payload: EventUpdateRequest,
  ): Promise<EventResponse> {
    const response = await httpClient.put<EventResponse>(
      `/admin/events/${eventId}`,
      payload,
    );

    return response.data;
  },

  async deleteEvent(eventId: string): Promise<void> {
    await httpClient.delete(`/admin/events/${eventId}`);
  },

  async updateEventStatus(
    eventId: string,
    status: EventStatus,
  ): Promise<EventResponse | { success: boolean; message: string; status: string }> {
    const response = await httpClient.put<EventResponse | { success: boolean; message: string; status: string }>(
      `/admin/events/${eventId}/status`,
      undefined,
      { params: { new_status: status } },
    );

    return response.data;
  },
};

export default eventApi;
