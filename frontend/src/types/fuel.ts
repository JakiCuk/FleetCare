export interface FuelRecord {
  id: number;
  refueled_at: string;
  odometer_km: number;
  liters: number;
  price_per_liter: number;
  total_cost: number;
  full_tank: boolean;
  consumption_l_100km: number | null;
}

export interface CreateFuelRecordRequest {
  refueled_at: string;
  odometer_km: number;
  liters: number;
  price_per_liter: number;
  total_cost?: number | null;
  full_tank: boolean;
}

export interface FuelMonthlyPoint {
  month: string;
  consumption: number;
}

export interface FuelStats {
  avg_consumption: number | null;
  total_spent: number;
  count: number;
  monthly: FuelMonthlyPoint[];
}
