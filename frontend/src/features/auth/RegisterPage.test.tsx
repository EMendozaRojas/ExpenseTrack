import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as api from "./api";
import { AuthProvider } from "./AuthContext";
import { RegisterPage } from "./RegisterPage";

vi.mock("./api");

function renderRegisterPage() {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={["/register"]}>
          <Routes>
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/" element={<p>Página principal</p>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  );
}

describe("RegisterPage", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetAllMocks();
  });

  it("valida que las contraseñas coincidan antes de enviar", async () => {
    const user = userEvent.setup();
    renderRegisterPage();

    await user.type(screen.getByLabelText("Email"), "demo@example.com");
    await user.type(screen.getByLabelText("Contraseña"), "secret123");
    await user.type(screen.getByLabelText("Confirmar contraseña"), "different123");
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("no coinciden");
    expect(api.register).not.toHaveBeenCalled();
  });

  it("registra e inicia sesión automáticamente", async () => {
    const user = userEvent.setup();
    vi.mocked(api.register).mockResolvedValue({
      id: 1,
      email: "demo@example.com",
      created_at: "2026-01-01T00:00:00Z",
    });
    vi.mocked(api.login).mockResolvedValue({ access_token: "abc123", token_type: "bearer" });
    vi.mocked(api.fetchCurrentUser).mockResolvedValue({
      id: 1,
      email: "demo@example.com",
      created_at: "2026-01-01T00:00:00Z",
    });

    renderRegisterPage();

    await user.type(screen.getByLabelText("Email"), "demo@example.com");
    await user.type(screen.getByLabelText("Contraseña"), "secret123");
    await user.type(screen.getByLabelText("Confirmar contraseña"), "secret123");
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));

    expect(await screen.findByText("Página principal")).toBeInTheDocument();
    expect(api.register).toHaveBeenCalledWith({
      email: "demo@example.com",
      password: "secret123",
    });
  });
});
