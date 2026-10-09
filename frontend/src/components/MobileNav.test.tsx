import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";

import { MobileNav } from "./MobileNav";

function renderMobileNav(path = "/", unreadCount = 0) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <MobileNav unreadCount={unreadCount} />
      <Routes>
        <Route path="/" element={<p>Pantalla Estadísticas</p>} />
        <Route path="/settings" element={<p>Pantalla Configuración</p>} />
        <Route path="/insights" element={<p>Pantalla Análisis</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("MobileNav", () => {
  it("muestra las 4 secciones principales y el botón Más", () => {
    renderMobileNav();

    const bar = screen.getByRole("navigation", { name: "Menú principal" });
    for (const label of ["Estadísticas", "Movimientos", "Presupuestos", "Metas"]) {
      expect(within(bar).getByRole("link", { name: new RegExp(label) })).toBeInTheDocument();
    }
    expect(within(bar).getByRole("button", { name: "Más" })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
    expect(screen.queryByRole("dialog", { name: "Más opciones" })).not.toBeInTheDocument();
  });

  it("Más abre el panel con las secciones secundarias y el contador", async () => {
    const user = userEvent.setup();
    renderMobileNav("/", 4);

    const more = screen.getByRole("button", { name: "Más (4 notificaciones sin leer)" });
    await user.click(more);

    expect(more).toHaveAttribute("aria-expanded", "true");
    const panel = screen.getByRole("dialog", { name: "Más opciones" });
    expect(within(panel).getByRole("link", { name: /Análisis/ })).toBeInTheDocument();
    expect(within(panel).getByRole("link", { name: /Configuración/ })).toBeInTheDocument();
    const notifications = within(panel).getByRole("link", { name: /Notificaciones/ });
    expect(within(notifications).getByText("4")).toBeInTheDocument();
  });

  it("elegir una sección cierra el panel y navega", async () => {
    const user = userEvent.setup();
    renderMobileNav();

    await user.click(screen.getByRole("button", { name: "Más" }));
    await user.click(screen.getByRole("link", { name: /Configuración/ }));

    expect(screen.getByText("Pantalla Configuración")).toBeInTheDocument();
    expect(screen.queryByRole("dialog", { name: "Más opciones" })).not.toBeInTheDocument();
  });

  it("tocar fuera o pulsar Escape cierra el panel sin cambiar de pantalla", async () => {
    const user = userEvent.setup();
    renderMobileNav();

    await user.click(screen.getByRole("button", { name: "Más" }));
    await user.click(screen.getByRole("button", { name: "Cerrar más opciones" }));
    expect(screen.queryByRole("dialog", { name: "Más opciones" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Más" }));
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog", { name: "Más opciones" })).not.toBeInTheDocument();
    expect(screen.getByText("Pantalla Estadísticas")).toBeInTheDocument();
  });

  it("Más aparece activo cuando la pantalla actual es una sección secundaria", () => {
    renderMobileNav("/insights");

    expect(screen.getByRole("button", { name: "Más" })).toHaveClass("mobile-nav-active");
    expect(screen.getByRole("link", { name: /Estadísticas/ })).not.toHaveClass("mobile-nav-active");
  });
});
