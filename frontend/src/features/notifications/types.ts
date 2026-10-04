export type NotificationType = "budget_warning" | "budget_exceeded" | "goal_near" | "goal_reached";

export interface Notification {
  id: number;
  type: NotificationType;
  title: string;
  body: string;
  related_id: number;
  is_read: boolean;
  created_at: string;
}

export interface UnreadCount {
  count: number;
}
