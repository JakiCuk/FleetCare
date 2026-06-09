// Shared primitives matching the API contract.

export type StatusColor = 'green' | 'yellow' | 'red' | 'gray';

export type ChipVariant =
  | 'green'
  | 'yellow'
  | 'red'
  | 'blue'
  | 'purple'
  | 'orange'
  | 'gray';

export type Locale = 'sk' | 'en';

export interface ApiError {
  detail: string;
}

export interface Paginated {
  limit?: number;
  offset?: number;
}

/** Optional date-range filter (yyyy-mm-dd) shared by fuel/expense endpoints. */
export interface DateRange {
  from_date?: string;
  to_date?: string;
}

export type StatGroupBy = 'month' | 'year';
