export interface STK {
  id: number;
  inspected_at: string;
  valid_until: string;
  cost: number | null;
  provider: string | null;
  note: string | null;
  days_left: number | null;
}

export interface CreateSTKRequest {
  inspected_at: string;
  valid_until: string;
  cost?: number | null;
  provider?: string | null;
  note?: string | null;
}

export type InsuranceType = 'PZP' | 'KASKO';

export interface Insurance {
  id: number;
  type: InsuranceType;
  provider: string | null;
  policy_number: string | null;
  valid_from: string | null;
  valid_until: string;
  cost: number | null;
  days_left: number | null;
}

export interface CreateInsuranceRequest {
  type: InsuranceType;
  provider?: string | null;
  policy_number?: string | null;
  valid_from?: string | null;
  valid_until: string;
  cost?: number | null;
}

export interface Vignette {
  id: number;
  country: string;
  valid_from: string | null;
  valid_until: string;
  cost: number | null;
  provider: string | null;
  days_left: number | null;
}

export interface CreateVignetteRequest {
  country: string;
  valid_from?: string | null;
  valid_until: string;
  cost?: number | null;
  provider?: string | null;
}

export interface DocumentsBundle {
  stk: STK[];
  insurance: Insurance[];
  vignettes: Vignette[];
}
