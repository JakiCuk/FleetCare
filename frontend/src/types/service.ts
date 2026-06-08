export type ServiceCategory = 'service' | 'repair' | 'tires' | 'other';

export interface ServiceRecord {
  id: number;
  performed_at: string;
  odometer_km: number;
  category: ServiceCategory;
  description: string;
  cost: number | null;
  shop?: string | null;
  warranty_until?: string | null;
  performed_items?: string[] | null;
  additional_work?: string[] | null;
  oil_name?: string | null;
  next_oil_change_km?: number | null;
  defect_found?: boolean | null;
  defect_description?: string | null;
  tire_action?: string | null;
  season?: string | null;
  create_reminder?: boolean | null;
  next_service_date?: string | null;
  next_service_km?: number | null;
  next_additional_date?: string | null;
  next_additional_km?: number | null;
}

export interface CreateServiceRecordRequest {
  performed_at: string;
  odometer_km: number;
  category: ServiceCategory;
  description: string;
  cost?: number | null;
  shop?: string | null;
  warranty_until?: string | null;
  performed_items?: string[];
  additional_work?: string[];
  oil_name?: string | null;
  next_oil_change_km?: number | null;
  defect_found?: boolean | null;
  defect_description?: string | null;
  tire_action?: string | null;
  season?: string | null;
  create_reminder?: boolean | null;
  next_service_date?: string | null;
  next_service_km?: number | null;
  next_additional_date?: string | null;
  next_additional_km?: number | null;
}

export interface ServiceInterval {
  id: number;
  name: string;
  interval_km: number | null;
  interval_months: number | null;
  last_performed_km: number | null;
  last_performed_at: string | null;
  next_due_km: number | null;
  next_due_date: string | null;
  km_left: number | null;
  days_left: number | null;
  is_active: boolean;
}

export interface CreateServiceIntervalRequest {
  name: string;
  interval_km?: number | null;
  interval_months?: number | null;
  last_performed_km?: number | null;
  last_performed_at?: string | null;
  is_active?: boolean;
}
