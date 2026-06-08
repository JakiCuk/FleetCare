import api from './client';
import type { CreateUserRequest, UpdateUserRequest, User } from '@/types';

export const usersApi = {
  list: () => api.get<User[]>('/users').then((r) => r.data),

  get: (id: number) => api.get<User>(`/users/${id}`).then((r) => r.data),

  create: (body: CreateUserRequest) =>
    api.post<User>('/users', body).then((r) => r.data),

  update: (id: number, body: UpdateUserRequest) =>
    api.patch<User>(`/users/${id}`, body).then((r) => r.data),

  remove: (id: number) => api.delete<void>(`/users/${id}`).then((r) => r.data),
};
