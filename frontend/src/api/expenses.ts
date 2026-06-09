import api from './client';
import type { CreateExpenseRequest, DateRange, Expense, ExpenseBreakdown } from '@/types';

export const expensesApi = {
  list: (carId: number, range?: DateRange) =>
    api.get<Expense[]>(`/cars/${carId}/expenses`, { params: range }).then((r) => r.data),

  create: (carId: number, body: CreateExpenseRequest) =>
    api.post<Expense>(`/cars/${carId}/expenses`, body).then((r) => r.data),

  update: (id: number, body: Partial<CreateExpenseRequest>) =>
    api.patch<Expense>(`/expenses/${id}`, body).then((r) => r.data),

  remove: (id: number) => api.delete<void>(`/expenses/${id}`).then((r) => r.data),

  breakdown: (carId: number, range?: DateRange) =>
    api
      .get<ExpenseBreakdown>(`/cars/${carId}/expenses/breakdown`, { params: range })
      .then((r) => r.data),
};
