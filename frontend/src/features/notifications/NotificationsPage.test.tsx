import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as notificationsApi from "./api";
import { NotificationsPage } from "./NotificationsPage";
import type { Notification } from "./types";

vi.mock("./api");
vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({ token: "test-token", user: { id: 1, email: "demo@example.com" } }),
}));

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <NotificationsPage />
    </QueryClientProvider>,
  );
}

const notifications: Notification[] = [
  {
    id: 1,
    type: "budget_warning",
    title: "Cerca del límite: Supermercado",
    body: "Vas en 85.00 de 100.00 en \"Supermercado\" este mes (85%).",
    related_id: 10,
    is_read: false,
    created_at: "2026-10-04T10:00:00Z",
  },
  {
    id: 2,
    type: "goal_reached",
    title: "¡Meta alcanzada!: Viaje",
    body: "Llegaste a tu meta \"Viaje\".",
    related_id: 5,
    is_read: true,
    created_at: "2026-10-03T10:00:00Z",
  },
];

describe("NotificationsPage", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("muestra un mensaje cuando no hay notificaciones", async () => {
    vi.mocked(notificationsApi.listNotifications).mockResolvedValue([]);

    renderPage();

    expect(await screen.findByText("No tienes notificaciones todavía.")).toBeInTheDocument();
  });

  it("lista las notificaciones y distingue las no leídas", async () => {
    vi.mocked(notificationsApi.listNotifications).mockResolvedValue(notifications);

    renderPage();

    expect(await screen.findByText("Cerca del límite: Supermercado")).toBeInTheDocument();
    expect(screen.getByText("¡Meta alcanzada!: Viaje")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Marcar leída" })).toHaveLength(1);
  });

  it("marca una notificación como leída", async () => {
    const user = userEvent.setup();
    vi.mocked(notificationsApi.listNotifications).mockResolvedValue(notifications);
    vi.mocked(notificationsApi.markNotificationRead).mockResolvedValue({
      ...notifications[0],
      is_read: true,
    });

    renderPage();
    await screen.findByText("Cerca del límite: Supermercado");

    await user.click(screen.getByRole("button", { name: "Marcar leída" }));

    expect(notificationsApi.markNotificationRead).toHaveBeenCalledWith("test-token", 1);
  });

  it("marca todas como leídas", async () => {
    const user = userEvent.setup();
    vi.mocked(notificationsApi.listNotifications).mockResolvedValue(notifications);
    vi.mocked(notificationsApi.markAllNotificationsRead).mockResolvedValue(undefined);

    renderPage();
    await screen.findByText("Cerca del límite: Supermercado");

    await user.click(screen.getByRole("button", { name: "Marcar todas como leídas" }));

    expect(notificationsApi.markAllNotificationsRead).toHaveBeenCalledWith("test-token");
  });
});
