import api from './client';
import type {
  CreateFuelRecordRequest,
  DateRange,
  FuelRecord,
  FuelStats,
  StatGroupBy,
} from '@/types';

export const fuelApi = {
  list: (carId: number, range?: DateRange) =>
    api.get<FuelRecord[]>(`/cars/${carId}/fuel`, { params: range }).then((r) => r.data),

  create: (carId: number, body: CreateFuelRecordRequest) =>
    api.post<FuelRecord>(`/cars/${carId}/fuel`, body).then((r) => r.data),

  update: (id: number, body: Partial<CreateFuelRecordRequest>) =>
    api.patch<FuelRecord>(`/fuel/${id}`, body).then((r) => r.data),

  remove: (id: number) => api.delete<void>(`/fuel/${id}`).then((r) => r.data),

  stats: (carId: number, params?: DateRange & { group_by?: StatGroupBy }) =>
    api.get<FuelStats>(`/cars/${carId}/fuel/stats`, { params }).then((r) => r.data),
};
