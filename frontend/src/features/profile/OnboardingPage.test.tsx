import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen } from "@testing-library/react";
import { useSyncExternalStore } from "react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as profileApi from "./api";
import { OnboardingPage } from "./OnboardingPage";

vi.mock("./api");

const refreshUserMock = vi.fn();
const useAuthMock = vi.fn();

vi.mock("../auth/useAuth", () => ({
  useAuth: () => useAuthMock(),
}));

function renderOnboardingPage() {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/onboarding"]}>
        <Routes>
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route path="/" element={<p>Página principal</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("OnboardingPage", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    useAuthMock.mockReturnValue({
      token: "test-token",
      user: { id: 1, email: "demo@example.com", full_name: null, has_avatar: false },
      refreshUser: refreshUserMock,
    });
  });

  it("guarda el nombre y redirige al dashboard", async () => {
    const user = userEvent.setup();
    vi.mocked(profileApi.updateProfile).mockResolvedValue({
      id: 1,
      email: "demo@example.com",
      full_name: "Ana López",
      has_avatar: false,
      created_at: "2026-01-01T00:00:00Z",
    });

    renderOnboardingPage();

    await user.type(screen.getByLabelText("Nombre"), "Ana López");
    await user.click(screen.getByRole("button", { name: "Continuar" }));

    expect(profileApi.updateProfile).toHaveBeenCalledWith("test-token", "Ana López");
    expect(profileApi.uploadAvatar).not.toHaveBeenCalled();
    expect(await screen.findByText("Página principal")).toBeInTheDocument();
  });

  it("tras guardar, cuando el usuario ya tiene nombre, redirige sin romperse", async () => {
    const user = userEvent.setup();
    vi.mocked(profileApi.updateProfile).mockResolvedValue({
      id: 1,
      email: "demo@example.com",
      full_name: "Ana López",
      has_avatar: false,
      created_at: "2026-01-01T00:00:00Z",
    });
    // Como en la app real: el usuario vive en un estado compartido y
    // refrescarlo vuelve a renderizar la página, ya con nombre.
    let auth = {
      token: "test-token",
      user: {
        id: 1,
        email: "demo@example.com",
        full_name: null as string | null,
        has_avatar: false,
      },
      refreshUser: refreshUserMock,
    };
    const listeners = new Set<() => void>();
    useAuthMock.mockImplementation(() =>
      useSyncExternalStore(
        (listener) => {
          listeners.add(listener);
          return () => listeners.delete(listener);
        },
        () => auth,
      ),
    );
    refreshUserMock.mockImplementation(async () => {
      auth = { ...auth, user: { ...auth.user, full_name: "Ana López" } };
      act(() => listeners.forEach((listener) => listener()));
    });

    renderOnboardingPage();

    await user.type(screen.getByLabelText("Nombre"), "Ana López");
    await user.click(screen.getByRole("button", { name: "Continuar" }));

    expect(await screen.findByText("Página principal")).toBeInTheDocument();
  });

  it("redirige directo al dashboard si el usuario ya tiene nombre", () => {
    useAuthMock.mockReturnValue({
      token: "test-token",
      user: { id: 1, email: "demo@example.com", full_name: "Ya tengo nombre", has_avatar: false },
      refreshUser: refreshUserMock,
    });

    renderOnboardingPage();

    expect(screen.getByText("Página principal")).toBeInTheDocument();
  });

  it("el botón continuar está deshabilitado sin nombre", () => {
    renderOnboardingPage();

    expect(screen.getByRole("button", { name: "Continuar" })).toBeDisabled();
  });
});
