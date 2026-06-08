import type { Locale } from './common';

export interface UserCarRef {
  id: number;
  name: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  is_admin: boolean;
  is_active: boolean;
  locale: Locale;
  cars: UserCarRef[];
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
  user: User;
}

export interface RefreshResponse {
  access_token: string;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  full_name: string;
  password: string;
  is_admin: boolean;
  locale: Locale;
  car_ids: number[];
}

export interface UpdateUserRequest {
  email?: string;
  full_name?: string;
  password?: string;
  is_admin?: boolean;
  is_active?: boolean;
  locale?: Locale;
  car_ids?: number[];
}
