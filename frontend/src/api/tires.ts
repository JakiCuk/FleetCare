import api from './client';
import type {
  CreateTireSetRequest,
  TireMeasurement,
  TireSet,
  TireTrend,
  UpdateTireSetRequest,
} from '@/types';

export const tiresApi = {
  list: (carId: number) =>
    api.get<TireSet[]>(`/cars/${carId}/tires`).then((r) => r.data),

  create: (carId: number, body: CreateTireSetRequest) =>
    api.post<TireSet>(`/cars/${carId}/tires`, body).then((r) => r.data),

  update: (setId: number, body: UpdateTireSetRequest) =>
    api.patch<TireSet>(`/tires/${setId}`, body).then((r) => r.data),

  remove: (setId: number) => api.delete<void>(`/tires/${setId}`).then((r) => r.data),

  addMeasurement: (setId: number, body: TireMeasurement) =>
    api.post<TireMeasurement>(`/tires/${setId}/measurements`, body).then((r) => r.data),

  trend: (setId: number) =>
    api.get<TireTrend>(`/tires/${setId}/trend`).then((r) => r.data),
};
