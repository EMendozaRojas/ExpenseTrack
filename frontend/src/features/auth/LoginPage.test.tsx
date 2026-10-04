import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as api from "./api";
import { AuthProvider } from "./AuthContext";
import { LoginPage } from "./LoginPage";

vi.mock("./api");

function renderLoginPage() {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={["/login"]}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<p>Página principal</p>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  );
}

describe("LoginPage", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetAllMocks();
  });

  it("navega a la página principal tras iniciar sesión correctamente", async () => {
    const user = userEvent.setup();
    vi.mocked(api.login).mockResolvedValue({ access_token: "abc123", token_type: "bearer" });
    vi.mocked(api.fetchCurrentUser).mockResolvedValue({
      id: 1,
      email: "demo@example.com",
      full_name: "Demo User",
      has_avatar: false,
      created_at: "2026-01-01T00:00:00Z",
    });

    renderLoginPage();

    await user.type(screen.getByLabelText("Email"), "demo@example.com");
    await user.type(screen.getByLabelText("Contraseña"), "secret123");
    await user.click(screen.getByRole("button", { name: "Ingresar" }));

    expect(await screen.findByText("Página principal")).toBeInTheDocument();
  });

  it("muestra un error cuando las credenciales son incorrectas", async () => {
    const user = userEvent.setup();
    const { ApiError } = await import("../../api/client");
    vi.mocked(api.login).mockRejectedValue(new ApiError(401, "Email o contraseña incorrectos"));

    renderLoginPage();

    await user.type(screen.getByLabelText("Email"), "demo@example.com");
    await user.type(screen.getByLabelText("Contraseña"), "wrong-password");
    await user.click(screen.getByRole("button", { name: "Ingresar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Email o contraseña incorrectos");
  });
});
