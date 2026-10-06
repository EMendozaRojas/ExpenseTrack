import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "../auth/useAuth";
import { listNotifications, markAllNotificationsRead, markNotificationRead } from "./api";
import type { Notification, NotificationType } from "./types";

const TYPE_ICON: Record<NotificationType, string> = {
  budget_warning: "⚠️",
  budget_exceeded: "🚨",
  budget_month_summary: "📅",
  budget_category_deleted: "🗂️",
  goal_near: "🏁",
  goal_reached: "🎉",
};

export function NotificationsPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  const notificationsQuery = useQuery({
    queryKey: ["notifications"],
    queryFn: () => listNotifications(token as string),
    enabled: token !== null,
  });

  const readMutation = useMutation({
    mutationFn: (notificationId: number) => markNotificationRead(token as string, notificationId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications"] });
      void queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
    },
  });

  const readAllMutation = useMutation({
    mutationFn: () => markAllNotificationsRead(token as string),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications"] });
      void queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
    },
  });

  const notifications = notificationsQuery.data ?? [];
  const hasUnread = notifications.some((n) => !n.is_read);

  return (
    <div className="notifications-page">
      <div className="notifications-header">
        <h1>Notificaciones</h1>
        <button
          type="button"
          className="button-secondary"
          disabled={!hasUnread || readAllMutation.isPending}
          onClick={() => readAllMutation.mutate()}
        >
          Marcar todas como leídas
        </button>
      </div>

      {notificationsQuery.isLoading && <p className="page-status">Cargando...</p>}
      {!notificationsQuery.isLoading && notifications.length === 0 && (
        <p className="page-status">No tienes notificaciones todavía.</p>
      )}

      <div className="notifications-list">
        {notifications.map((notification: Notification) => (
          <div
            key={notification.id}
            className={`notification-card ${notification.is_read ? "" : "notification-card-unread"}`}
          >
            <span className="notification-card-icon" aria-hidden="true">
              {TYPE_ICON[notification.type]}
            </span>
            <div className="notification-card-body">
              <span className="notification-card-title">{notification.title}</span>
              <span className="page-status">{notification.body}</span>
              <span className="notification-card-date">
                {new Date(notification.created_at).toLocaleString("es-ES")}
              </span>
            </div>
            {!notification.is_read && (
              <button
                type="button"
                className="button-secondary"
                disabled={readMutation.isPending}
                onClick={() => readMutation.mutate(notification.id)}
              >
                Marcar leída
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
