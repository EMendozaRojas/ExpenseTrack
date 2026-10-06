import { apiFetch } from "../../api/client";
import type { Notification, UnreadCount } from "./types";

export function listNotifications(token: string): Promise<Notification[]> {
  return apiFetch<Notification[]>("/notifications/", token);
}

export function getUnreadCount(token: string): Promise<UnreadCount> {
  return apiFetch<UnreadCount>("/notifications/unread-count", token);
}

export function markNotificationRead(token: string, notificationId: number): Promise<Notification> {
  return apiFetch<Notification>(`/notifications/${notificationId}/read`, token, {
    method: "POST",
  });
}

export function markAllNotificationsRead(token: string): Promise<void> {
  return apiFetch<void>("/notifications/read-all", token, { method: "POST" });
}

/** Revisión al entrar a la app: crea los avisos de presupuesto que falten y
 * el resumen de cierre del mes anterior. */
export function checkNotifications(token: string): Promise<void> {
  return apiFetch<void>("/notifications/check", token, { method: "POST" });
}
