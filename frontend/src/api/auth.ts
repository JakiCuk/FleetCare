import api from './client';
import type { LoginRequest, LoginResponse, RefreshResponse, User } from '@/types';

export const authApi = {
  login: (body: LoginRequest) =>
    api.post<LoginResponse>('/auth/login', body).then((r) => r.data),

  refresh: () => api.post<RefreshResponse>('/auth/refresh', {}).then((r) => r.data),

  logout: () => api.post<void>('/auth/logout').then((r) => r.data),

  me: () => api.get<User>('/auth/me').then((r) => r.data),
};
