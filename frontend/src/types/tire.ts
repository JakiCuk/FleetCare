export type TireSeason = 'summer' | 'winter' | 'all_season';

export interface TireMeasurement {
  id?: number;
  measured_at: string;
  odometer_km: number;
  tread_fl_mm: number;
  tread_fr_mm: number;
  tread_rl_mm: number;
  tread_rr_mm: number;
  pressure_fl_before_bar?: number | null;
  pressure_fr_before_bar?: number | null;
  pressure_rl_before_bar?: number | null;
  pressure_rr_before_bar?: number | null;
  pressure_fl_after_bar?: number | null;
  pressure_fr_after_bar?: number | null;
  pressure_rl_after_bar?: number | null;
  pressure_rr_after_bar?: number | null;
}

export interface TireSet {
  id: number;
  name: string;
  season: TireSeason;
  is_active: boolean;
  mounted_at: string | null;
  mounted_odometer_km: number | null;
  expected_change_date: string | null;
  avg_tread_mm: number | null;
  mileage_km: number | null;
  avg_pressure_bar: number | null;
  projection_date: string | null;
  measurements: TireMeasurement[];
}

export interface CreateTireSetRequest {
  name: string;
  season: TireSeason;
  mounted_at?: string | null;
  mounted_odometer_km?: number | null;
  expected_change_date?: string | null;
  initial_measurement?: TireMeasurement;
}

export type UpdateTireSetRequest = Partial<Omit<CreateTireSetRequest, 'initial_measurement'>> & {
  is_active?: boolean;
};

export interface TireTrendPoint {
  km: number;
  actual?: number;
  projected?: number;
}

export interface TireTrend {
  points: { km: number; actual: number }[];
  projection: { km: number; projected: number }[];
  reference_mm: number;
  projection_date: string | null;
  /** km at which the 1.6 mm reference is reached (present even without a date). */
  km_at_reference: number | null;
}
