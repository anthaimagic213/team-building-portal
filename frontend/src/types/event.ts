export type EventStatus =
  | 'DRAFT'
  | 'REGISTRATION_OPEN'
  | 'REGISTRATION_CLOSED'
  | 'ALLOCATION_IN_PROGRESS'
  | 'ALLOCATION_COMPLETED'
  | 'EVENT_ACTIVE'
  | 'EVENT_COMPLETED';

export interface EventBase {
  event_name: string;
  event_date_start: string;
  event_date_end: string;
  location: string;
  registration_deadline: string;
  description?: string | null;
}

export type EventCreateRequest = EventBase;


export interface EventUpdateRequest {
  event_name?: string;
  event_date_start?: string;
  event_date_end?: string;
  location?: string;
  registration_deadline?: string;
  description?: string | null;
  status?: EventStatus;
}

export interface EventResponse extends EventBase {
  id: string;
  status: EventStatus;
  total_participants: number;
  created_at: string;
}

export interface ActiveEventResponse extends EventResponse {
  is_registration_open?: boolean;
  is_information_published?: boolean;
}
