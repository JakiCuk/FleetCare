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

/** Compact active-tire-set summary embedded in CarDetail (full set via /tires). */
export interface ActiveTireSetSummary {
  id: number;
  name: string;
  season: string;
  avg_tread_mm: number | null;
  projection_date: string | null;
}

/** Compact document validity summary embedded in the enriched cars list. */
export interface CarDocStatus {
  valid_until: string;
  days_left: number;
}

/** GET /api/cars list item: base Car + STK/insurance summaries + overdue flag. */
export interface CarListItem extends Car {
  stk: CarDocStatus | null;
  pzp: CarDocStatus | null;
  kasko: CarDocStatus | null;
  overdue: boolean;
}

export interface CarDetail extends Car {
  stk: DocumentSummary | null;
  pzp: DocumentSummary | null;
  kasko: DocumentSummary | null;
  vignettes: VignetteSummary[];
  active_tire_set: ActiveTireSetSummary | null;
  next_service: NextServiceSummary | null;
  overdue: boolean;
  monthly_cost: number;
}

export interface CreateCarRequest {
  /** Optional — the server derives "make model" when omitted. */
  name?: string;
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
