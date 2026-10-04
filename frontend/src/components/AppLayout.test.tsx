import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as notificationsApi from "../features/notifications/api";
import { AppLayout } from "./AppLayout";

const logoutMock = vi.fn();
const useAuthMock = vi.fn();

vi.mock("../features/auth/useAuth", () => ({
  useAuth: () => useAuthMock(),
}));
vi.mock("../features/notifications/api");

function renderAppLayout() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<p>Contenido</p>} />
          </Route>
          <Route path="/login" element={<p>Login</p>} />
          <Route path="/onboarding" element={<p>Onboarding</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AppLayout", () => {
  beforeEach(() => {
    vi.mocked(notificationsApi.getUnreadCount).mockResolvedValue({ count: 0 });
  });

  it("muestra el nombre del usuario y cierra sesión al hacer clic", async () => {
    const user = userEvent.setup();
    useAuthMock.mockReturnValue({
      user: { id: 1, email: "demo@example.com", full_name: "Demo User", has_avatar: false },
      token: "test-token",
      logout: logoutMock,
    });

    renderAppLayout();

    expect(screen.getByText("Demo User")).toBeInTheDocument();
    expect(screen.getByText("Contenido")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Cerrar sesión" }));

    expect(logoutMock).toHaveBeenCalled();
    expect(await screen.findByText("Login")).toBeInTheDocument();
  });

  it("redirige a onboarding si el usuario no tiene nombre guardado", async () => {
    useAuthMock.mockReturnValue({
      user: { id: 1, email: "demo@example.com", full_name: null, has_avatar: false },
      token: "test-token",
      logout: logoutMock,
    });

    renderAppLayout();

    expect(await screen.findByText("Onboarding")).toBeInTheDocument();
  });

  it("muestra el contador de notificaciones no leídas en el menú y en la campana superior", async () => {
    useAuthMock.mockReturnValue({
      user: { id: 1, email: "demo@example.com", full_name: "Demo User", has_avatar: false },
      token: "test-token",
      logout: logoutMock,
    });
    vi.mocked(notificationsApi.getUnreadCount).mockResolvedValue({ count: 3 });

    renderAppLayout();

    expect((await screen.findAllByText("3")).length).toBe(2);
  });

  it("muestra el botón de cerrar sesión en la barra superior, no en el menú", async () => {
    useAuthMock.mockReturnValue({
      user: { id: 1, email: "demo@example.com", full_name: "Demo User", has_avatar: false },
      token: "test-token",
      logout: logoutMock,
    });

    renderAppLayout();

    const logoutButton = await screen.findByRole("button", { name: "Cerrar sesión" });
    expect(logoutButton.closest(".app-topbar")).not.toBeNull();
    expect(logoutButton.closest(".app-sidebar")).toBeNull();
  });
});
