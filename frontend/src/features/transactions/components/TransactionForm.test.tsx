import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { Account, Category } from "../types";
import { TransactionForm } from "./TransactionForm";

const accounts: Account[] = [
  {
    id: 1,
    owner_id: 1,
    name: "Efectivo",
    type: "cash",
    currency: "EUR",
    initial_balance: "0.00",
    balance: "0.00",
    is_archived: false,
    is_primary: true,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
];

const categories: Category[] = [
  {
    id: 1,
    name: "Comida",
    owner_id: null,
    parent_id: null,
    kind: "expense",
    icon: null,
    color: null,
    is_system: true,
    is_fixed: false,
    created_at: "2026-01-01T00:00:00Z",
    children: [],
  },
];

describe("TransactionForm", () => {
  it("muestra un error si el monto no es válido", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <TransactionForm
        accounts={accounts}
        categories={categories}
        defaultDate="2026-08-13"
        onSubmit={onSubmit}
        onCreateCategory={vi.fn()}
        isSubmitting={false}
      />,
    );

    await user.type(screen.getByLabelText("Monto"), "0");
    await user.click(screen.getByRole("button", { name: "Agregar movimiento" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("monto válido");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("envía un gasto con importe negativo", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <TransactionForm
        accounts={accounts}
        categories={categories}
        defaultDate="2026-08-13"
        onSubmit={onSubmit}
        onCreateCategory={vi.fn()}
        isSubmitting={false}
      />,
    );

    await user.type(screen.getByLabelText("Monto"), "25.5");
    await user.type(screen.getByLabelText("Descripción"), "Cena");
    await user.selectOptions(screen.getByLabelText("Categoría"), "Comida");
    await user.click(screen.getByRole("button", { name: "Agregar movimiento" }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith({
        account_id: 1,
        amount: "-25.50",
        direction: "expense",
        posted_at: "2026-08-13",
        category_id: 1,
        note: "Cena",
      }),
    );
  });

  it("envía un ingreso con importe positivo", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <TransactionForm
        accounts={accounts}
        categories={categories}
        defaultDate="2026-08-13"
        onSubmit={onSubmit}
        onCreateCategory={vi.fn()}
        isSubmitting={false}
      />,
    );

    await user.click(screen.getByLabelText("Ingreso"));
    await user.type(screen.getByLabelText("Monto"), "1200");
    await user.click(screen.getByRole("button", { name: "Agregar movimiento" }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ amount: "1200.00", direction: "income" }),
      ),
    );
  });

  it("crea una categoría nueva antes de enviar el movimiento", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const onCreateCategory = vi.fn().mockResolvedValue({
      id: 99,
      name: "Viajes",
      owner_id: 1,
      parent_id: null,
      kind: "expense",
      icon: null,
      color: null,
      is_system: false,
      is_fixed: false,
      created_at: "2026-08-13T00:00:00Z",
      children: [],
    });

    render(
      <TransactionForm
        accounts={accounts}
        categories={categories}
        defaultDate="2026-08-13"
        onSubmit={onSubmit}
        onCreateCategory={onCreateCategory}
        isSubmitting={false}
      />,
    );

    await user.type(screen.getByLabelText("Monto"), "100");
    await user.selectOptions(screen.getByLabelText("Categoría"), "+ Nueva categoría");
    await user.type(screen.getByLabelText("Nombre de la categoría"), "Viajes");
    await user.click(screen.getByRole("button", { name: "Agregar movimiento" }));

    await waitFor(() => expect(onCreateCategory).toHaveBeenCalledWith("Viajes"));
    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ category_id: 99 })),
    );
  });

  it("con una sola cuenta no muestra el campo Cuenta", () => {
    render(
      <TransactionForm
        accounts={accounts}
        categories={categories}
        defaultDate="2026-08-13"
        onSubmit={vi.fn()}
        onCreateCategory={vi.fn()}
        isSubmitting={false}
      />,
    );

    expect(screen.queryByLabelText("Cuenta")).not.toBeInTheDocument();
  });

  it("con varias cuentas muestra el campo Cuenta con la primera elegida", () => {
    render(
      <TransactionForm
        accounts={[...accounts, { ...accounts[0], id: 2, name: "Ahorros", is_primary: false }]}
        categories={categories}
        defaultDate="2026-08-13"
        onSubmit={vi.fn()}
        onCreateCategory={vi.fn()}
        isSubmitting={false}
      />,
    );

    expect(screen.getByLabelText("Cuenta")).toHaveValue("1");
  });
});
