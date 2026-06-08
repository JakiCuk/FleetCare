import api from './client';
import type {
  CreateInsuranceRequest,
  CreateSTKRequest,
  CreateVignetteRequest,
  DocumentsBundle,
  Insurance,
  STK,
  Vignette,
} from '@/types';

export const documentsApi = {
  bundle: (carId: number) =>
    api.get<DocumentsBundle>(`/cars/${carId}/documents`).then((r) => r.data),

  // STK
  listStk: (carId: number) =>
    api.get<STK[]>(`/cars/${carId}/stk`).then((r) => r.data),
  createStk: (carId: number, body: CreateSTKRequest) =>
    api.post<STK>(`/cars/${carId}/stk`, body).then((r) => r.data),
  updateStk: (id: number, body: Partial<CreateSTKRequest>) =>
    api.patch<STK>(`/stk/${id}`, body).then((r) => r.data),
  removeStk: (id: number) => api.delete<void>(`/stk/${id}`).then((r) => r.data),

  // Insurance
  listInsurance: (carId: number) =>
    api.get<Insurance[]>(`/cars/${carId}/insurance`).then((r) => r.data),
  createInsurance: (carId: number, body: CreateInsuranceRequest) =>
    api.post<Insurance>(`/cars/${carId}/insurance`, body).then((r) => r.data),
  updateInsurance: (id: number, body: Partial<CreateInsuranceRequest>) =>
    api.patch<Insurance>(`/insurance/${id}`, body).then((r) => r.data),
  removeInsurance: (id: number) =>
    api.delete<void>(`/insurance/${id}`).then((r) => r.data),

  // Vignettes
  listVignettes: (carId: number) =>
    api.get<Vignette[]>(`/cars/${carId}/vignettes`).then((r) => r.data),
  createVignette: (carId: number, body: CreateVignetteRequest) =>
    api.post<Vignette>(`/cars/${carId}/vignettes`, body).then((r) => r.data),
  updateVignette: (id: number, body: Partial<CreateVignetteRequest>) =>
    api.patch<Vignette>(`/vignettes/${id}`, body).then((r) => r.data),
  removeVignette: (id: number) =>
    api.delete<void>(`/vignettes/${id}`).then((r) => r.data),
};
