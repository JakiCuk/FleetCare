import api from './client';
import type {
  CreateNotificationRuleRequest,
  NotificationLogEntry,
  NotificationLogStatus,
  NotificationRule,
  TestSendRequest,
  TestSendResponse,
} from '@/types';

export const notificationsApi = {
  // Rules
  listRules: (carId?: number) =>
    api
      .get<NotificationRule[]>('/notification-rules', {
        params: carId ? { car_id: carId } : undefined,
      })
      .then((r) => r.data),
  createRule: (body: CreateNotificationRuleRequest) =>
    api.post<NotificationRule>('/notification-rules', body).then((r) => r.data),
  updateRule: (id: number, body: Partial<CreateNotificationRuleRequest> & { is_active?: boolean }) =>
    api.patch<NotificationRule>(`/notification-rules/${id}`, body).then((r) => r.data),
  removeRule: (id: number) =>
    api.delete<void>(`/notification-rules/${id}`).then((r) => r.data),

  // Log
  listLog: (params?: { limit?: number; status?: NotificationLogStatus }) =>
    api.get<NotificationLogEntry[]>('/notification-log', { params }).then((r) => r.data),
  exportCsvUrl: () => `${import.meta.env.VITE_API_BASE || '/api'}/notification-log/export.csv`,

  // Test / run
  test: (body: TestSendRequest) =>
    api.post<TestSendResponse>('/notifications/test', body).then((r) => r.data),
  run: () => api.post<void>('/notifications/run').then((r) => r.data),
};
