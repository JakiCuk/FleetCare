import api from './client';
import type { CreateFuelRecordRequest, FuelRecord, FuelStats } from '@/types';

export const fuelApi = {
  list: (carId: number) =>
    api.get<FuelRecord[]>(`/cars/${carId}/fuel`).then((r) => r.data),

  create: (carId: number, body: CreateFuelRecordRequest) =>
    api.post<FuelRecord>(`/cars/${carId}/fuel`, body).then((r) => r.data),

  update: (id: number, body: Partial<CreateFuelRecordRequest>) =>
    api.patch<FuelRecord>(`/fuel/${id}`, body).then((r) => r.data),

  remove: (id: number) => api.delete<void>(`/fuel/${id}`).then((r) => r.data),

  stats: (carId: number) =>
    api.get<FuelStats>(`/cars/${carId}/fuel/stats`).then((r) => r.data),
};
