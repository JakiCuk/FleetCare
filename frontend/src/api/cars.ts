import api from './client';
import type {
  Car,
  CarDetail,
  CarListItem,
  CreateCarRequest,
  CreateOdometerRequest,
  OdometerReading,
  UpdateCarRequest,
} from '@/types';

export const carsApi = {
  list: () => api.get<CarListItem[]>('/cars').then((r) => r.data),

  get: (id: number) => api.get<CarDetail>(`/cars/${id}`).then((r) => r.data),

  create: (body: CreateCarRequest) =>
    api.post<Car>('/cars', body).then((r) => r.data),

  update: (id: number, body: UpdateCarRequest) =>
    api.patch<Car>(`/cars/${id}`, body).then((r) => r.data),

  remove: (id: number) => api.delete<void>(`/cars/${id}`).then((r) => r.data),

  // Odometer
  odometer: (id: number) =>
    api.get<OdometerReading[]>(`/cars/${id}/odometer`).then((r) => r.data),

  addOdometer: (id: number, body: CreateOdometerRequest) =>
    api.post<OdometerReading>(`/cars/${id}/odometer`, body).then((r) => r.data),
};
