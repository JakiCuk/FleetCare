import api from './client';
import type {
  CreateServiceIntervalRequest,
  CreateServiceRecordRequest,
  ServiceInterval,
  ServiceRecord,
} from '@/types';

export const servicesApi = {
  // Records
  list: (carId: number) =>
    api.get<ServiceRecord[]>(`/cars/${carId}/services`).then((r) => r.data),
  create: (carId: number, body: CreateServiceRecordRequest) =>
    api.post<ServiceRecord>(`/cars/${carId}/services`, body).then((r) => r.data),
  update: (id: number, body: Partial<CreateServiceRecordRequest>) =>
    api.patch<ServiceRecord>(`/services/${id}`, body).then((r) => r.data),
  remove: (id: number) => api.delete<void>(`/services/${id}`).then((r) => r.data),

  // Intervals
  listIntervals: (carId: number) =>
    api.get<ServiceInterval[]>(`/cars/${carId}/service-intervals`).then((r) => r.data),
  createInterval: (carId: number, body: CreateServiceIntervalRequest) =>
    api
      .post<ServiceInterval>(`/cars/${carId}/service-intervals`, body)
      .then((r) => r.data),
  updateInterval: (id: number, body: Partial<CreateServiceIntervalRequest>) =>
    api.patch<ServiceInterval>(`/service-intervals/${id}`, body).then((r) => r.data),
  removeInterval: (id: number) =>
    api.delete<void>(`/service-intervals/${id}`).then((r) => r.data),
};
