import api from './client';
import type {
  AppSettings,
  TestStatusResponse,
  UpdateSettingsRequest,
} from '@/types';

export const settingsApi = {
  get: () => api.get<AppSettings>('/settings').then((r) => r.data),

  update: (body: UpdateSettingsRequest) =>
    api.put<AppSettings>('/settings', body).then((r) => r.data),

  testSmtp: () =>
    api.post<TestStatusResponse>('/settings/smtp/test').then((r) => r.data),

  testMatrix: () =>
    api.post<TestStatusResponse>('/settings/matrix/test').then((r) => r.data),

  exportUrl: () => `${import.meta.env.VITE_API_BASE || '/api'}/settings/export`,

  wipe: () => api.post<void>('/settings/wipe').then((r) => r.data),
};
