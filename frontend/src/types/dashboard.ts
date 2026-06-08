export interface DashboardChip {
  label: string;
  days_left: number | null;
}

export interface DashboardCar {
  id: number;
  name: string;
  license_plate: string;
  current_odometer_km: number;
  chips: DashboardChip[];
  next_service: string | null;
  tires: string | null;
  overdue: boolean;
}

export interface DashboardStats {
  cars: number;
  notifications_today: number;
  overdue_items: number;
  monthly_cost: number;
}

export interface Dashboard {
  stats: DashboardStats;
  cars: DashboardCar[];
}
