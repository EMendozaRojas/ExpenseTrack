import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { ProtectedRoute } from "./ProtectedRoute";

const useAuthMock = vi.fn();

vi.mock("../features/auth/useAuth", () => ({
  useAuth: () => useAuthMock(),
}));

function renderProtectedRoute() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<p>Contenido protegido</p>} />
        </Route>
        <Route path="/login" element={<p>Login</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute", () => {
  it("muestra un estado de carga mientras se restaura la sesión", () => {
    useAuthMock.mockReturnValue({ user: null, isLoading: true });

    renderProtectedRoute();

    expect(screen.getByText("Cargando...")).toBeInTheDocument();
  });

  it("redirige a login cuando no hay usuario autenticado", async () => {
    useAuthMock.mockReturnValue({ user: null, isLoading: false });

    renderProtectedRoute();

    expect(await screen.findByText("Login")).toBeInTheDocument();
  });

  it("renderiza el contenido cuando hay un usuario autenticado", () => {
    useAuthMock.mockReturnValue({ user: { id: 1, email: "demo@example.com" }, isLoading: false });

    renderProtectedRoute();

    expect(screen.getByText("Contenido protegido")).toBeInTheDocument();
  });
});
