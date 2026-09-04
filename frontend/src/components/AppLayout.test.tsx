import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { AppLayout } from "./AppLayout";

const logoutMock = vi.fn();

vi.mock("../features/auth/useAuth", () => ({
  useAuth: () => ({
    user: { id: 1, email: "demo@example.com" },
    logout: logoutMock,
  }),
}));

describe("AppLayout", () => {
  it("muestra el email del usuario y cierra sesión al hacer clic", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<p>Contenido</p>} />
          </Route>
          <Route path="/login" element={<p>Login</p>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("demo@example.com")).toBeInTheDocument();
    expect(screen.getByText("Contenido")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Cerrar sesión" }));

    expect(logoutMock).toHaveBeenCalled();
    expect(await screen.findByText("Login")).toBeInTheDocument();
  });
});
