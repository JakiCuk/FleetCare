export type ExpenseCategory = 'fuel' | 'service' | 'documents' | 'tires' | 'other';

export interface Expense {
  id: number;
  occurred_at: string;
  description: string;
  amount: number;
  category: ExpenseCategory;
}

export interface CreateExpenseRequest {
  occurred_at: string;
  description: string;
  amount: number;
  category: ExpenseCategory;
}

export interface ExpenseBreakdownItem {
  category: ExpenseCategory;
  amount: number;
}

export interface ExpenseBreakdown {
  total: number;
  breakdown: ExpenseBreakdownItem[];
}
