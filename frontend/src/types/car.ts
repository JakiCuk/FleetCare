import type { TireSet } from './tire';

export interface Car {
  id: number;
  name: string;
  full_name: string;
  make: string;
  model: string;
  year: number;
  license_plate: string;
  vin: string;
  current_odometer_km: number;
}

export interface DocumentSummary {
  id: number;
  valid_until: string | null;
  days_left: number | null;
  status?: string;
  provider?: string | null;
}

export interface VignetteSummary {
  id: number;
  country: string;
  valid_until: string | null;
  days_left: number | null;
}

export interface NextServiceSummary {
  name: string;
  km_left: number | null;
  days_left: number | null;
  label: string;
}

export interface CarDetail extends Car {
  stk: DocumentSummary | null;
  pzp: DocumentSummary | null;
  kasko: DocumentSummary | null;
  vignettes: VignetteSummary[];
  active_tire_set: TireSet | null;
  next_service: NextServiceSummary | null;
  overdue: boolean;
  monthly_cost: number;
}

export interface CreateCarRequest {
  name: string;
  make: string;
  model: string;
  year: number;
  license_plate: string;
  vin: string;
  current_odometer_km: number;
}

export type UpdateCarRequest = Partial<CreateCarRequest>;

export interface OdometerReading {
  id: number;
  reading_km: number;
  recorded_at: string;
  note: string | null;
}

export interface CreateOdometerRequest {
  reading_km: number;
  recorded_at?: string;
  note?: string;
}
