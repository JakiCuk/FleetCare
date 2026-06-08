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
