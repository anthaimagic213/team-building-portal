import httpClient from './httpClient';

export type NotificationType =
  | 'INFO'
  | 'WARNING'
  | 'URGENT'
  | string;

export interface NotificationCreateRequest {
  event_id: string;
  title: string;
  content: string;
  notification_type: NotificationType;
}

export interface NotificationResponse {
  id: string;
  event_id: string;
  title: string;
  content: string;
  notification_type: NotificationType;
  created_at: string;
  updated_at?: string | null;
}

export interface NotificationListResponse {
  notifications: NotificationResponse[];
  total?: number;
}

export const notificationApi = {
  async createNotification(
    payload: NotificationCreateRequest,
  ): Promise<NotificationResponse> {
    const response = await httpClient.post<NotificationResponse>(
      '/admin/notifications/',
      payload,
    );

    return response.data;
  },

  async listNotifications(
    eventId: string,
  ): Promise<NotificationListResponse> {
    const response = await httpClient.get<NotificationListResponse>(
      `/admin/notifications/${eventId}`,
    );

    return response.data;
  },
};

export default notificationApi;
