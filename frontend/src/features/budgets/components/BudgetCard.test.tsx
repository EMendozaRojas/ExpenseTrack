import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { BudgetWithStatus } from "../../transactions/types";
import { BudgetCard } from "./BudgetCard";

function budget(overrides: Partial<BudgetWithStatus> = {}): BudgetWithStatus {
  return {
    category_id: 94,
    category_name: "Alimentación",
    category_icon: "🛒",
    month: "2026-10",
    amount: "600.00",
    repeats: true,
    source: "series",
    editable: true,
    spent: "340.50",
    pct: 56.8,
    status: "ok",
    pace: { projected: "1172.83", will_exceed: true },
    ...overrides,
  };
}

describe("BudgetCard", () => {
  it("muestra nombre, etiqueta, importes, porcentaje, estado y ritmo", () => {
    const { container } = render(
      <BudgetCard budget={budget()} onEdit={vi.fn()} onDelete={vi.fn()} />,
    );

    expect(screen.getByText(/Alimentación/)).toBeInTheDocument();
    expect(screen.getByText("Se repite cada mes")).toBeInTheDocument();
    expect(container.querySelector(".budget-card-spent")).toHaveTextContent("340,50 €");
    expect(container.querySelector(".budget-card-amounts")).toHaveTextContent("600,00 €");
    // El porcentaje va junto al importe en el móvil y junto al estado en el ordenador.
    expect(container.querySelector(".budget-card-pct")).toHaveTextContent("56.8%");
    expect(container.querySelector(".budget-card-status")).toHaveTextContent(
      "Dentro del presupuesto · 56.8%",
    );
    expect(screen.getByText(/A este ritmo acabarás el mes en 1172,83/)).toBeInTheDocument();
  });

  it("usa el color del estado en el porcentaje", () => {
    const { container } = render(
      <BudgetCard
        budget={budget({ status: "exceeded", pct: 113.3, repeats: false })}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(container.querySelector(".budget-card-pct")).toHaveClass("budget-card-status-exceeded");
    expect(screen.getByText("Solo este mes")).toBeInTheDocument();
  });

  it("Editar y Borrar solo aparecen si el presupuesto es editable", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    const { rerender } = render(
      <BudgetCard budget={budget()} onEdit={onEdit} onDelete={vi.fn()} />,
    );

    await user.click(screen.getByRole("button", { name: "Editar" }));
    expect(onEdit).toHaveBeenCalled();

    rerender(
      <BudgetCard budget={budget({ editable: false })} onEdit={onEdit} onDelete={vi.fn()} />,
    );
    expect(screen.queryByRole("button", { name: "Editar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Borrar" })).not.toBeInTheDocument();
  });
});
