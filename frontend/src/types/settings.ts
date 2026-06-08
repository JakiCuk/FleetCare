import type { Locale } from './common';

export type SmtpEncryption = 'tls' | 'ssl' | 'none';

export interface SmtpSettings {
  host: string | null;
  port: number | null;
  encryption: SmtpEncryption;
  username: string | null;
  from: string | null;
  password_set: boolean;
}

export interface MatrixSettings {
  enabled: boolean;
  homeserver: string | null;
  default_room: string | null;
  token_set: boolean;
}

export interface DefaultLeadDays {
  1: number;
  2: number;
  3: number;
}

export interface AppSettings {
  fleet_name: string;
  timezone: string;
  default_locale: Locale;
  currency: string;
  default_lead_days: DefaultLeadDays;
  daily_send_time: string;
  tire_min_tread_mm: number;
  smtp: SmtpSettings;
  matrix: MatrixSettings;
}

export interface UpdateSettingsRequest {
  fleet_name?: string;
  timezone?: string;
  default_locale?: Locale;
  currency?: string;
  default_lead_days?: Partial<DefaultLeadDays>;
  daily_send_time?: string;
  tire_min_tread_mm?: number;
  smtp?: Partial<Omit<SmtpSettings, 'password_set'>> & { password?: string };
  matrix?: Partial<Omit<MatrixSettings, 'token_set'>> & { token?: string };
}

export interface TestStatusResponse {
  status: string;
}
