export type NotificationChannel = 'email' | 'matrix';

export interface NotificationRule {
  id: number;
  car_id: number;
  car_name: string;
  item_type: string;
  lead_days_1: number | null;
  lead_days_2: number | null;
  lead_days_3: number | null;
  is_active: boolean;
  is_smart: boolean;
  channel_email: boolean;
  channel_matrix: boolean;
  status: string;
}

export interface CreateNotificationRuleRequest {
  car_id: number;
  item_type: string;
  lead_days_1?: number | null;
  lead_days_2?: number | null;
  lead_days_3?: number | null;
  is_active?: boolean;
  is_smart?: boolean;
  channel_email?: boolean;
  channel_matrix?: boolean;
}

export type NotificationLogStatus = 'sent' | 'failed' | 'pending' | 'skipped';

export interface NotificationLogEntry {
  id: number;
  sent_at: string;
  car_name: string;
  item_type: string;
  channel: NotificationChannel;
  recipient: string;
  status: NotificationLogStatus;
  subject: string;
}

export interface TestSendRequest {
  channel: NotificationChannel;
  car_id?: number;
  to?: string;
}

export interface TestSendResponse {
  status: string;
}
