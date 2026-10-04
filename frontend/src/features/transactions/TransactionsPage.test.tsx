import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as preferencesApi from "../preferences/api";
import * as api from "./api";
import { TransactionsPage } from "./TransactionsPage";
import type { Account, TransactionPage } from "./types";

vi.mock("./api");
vi.mock("../preferences/api");
vi.mock("../imports/api");
vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({ token: "test-token", user: { id: 1, email: "demo@example.com" } }),
}));

const accounts: Account[] = [
  {
    id: 1,
    owner_id: 1,
    name: "Efectivo",
    type: "cash",
    currency: "EUR",
    initial_balance: "0.00",
    balance: "45.50",
    is_archived: false,
    is_primary: true,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
];

const categories = [
  {
    id: 1,
    name: "Comida",
    owner_id: null,
    parent_id: null,
    kind: "expense" as const,
    icon: null,
    color: null,
    is_system: true,
    is_fixed: false,
    created_at: "2026-01-01T00:00:00Z",
    children: [],
  },
];

const transactions: TransactionPage = {
  items: [
    {
      id: 1,
      account_id: 1,
      owner_id: 1,
      amount: "-45.50",
      direction: "expense",
      posted_at: "2026-08-10",
      category_id: 1,
      counterparty: null,
      raw_description: null,
      note: "Supermercado",
      source: "manual",
      transfer_group_id: null,
      created_at: "2026-08-10T00:00:00Z",
      updated_at: "2026-08-10T00:00:00Z",
    },
  ],
  next_cursor: null,
};

const summary = {
  year: 2026,
  month: 8,
  total: "45.50",
  by_category: [{ category_id: 1, category_name: "Comida", total: "45.50" }],
};

function renderPage() {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <TransactionsPage />
    </QueryClientProvider>,
  );
}

describe("TransactionsPage", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(api.listAccounts).mockResolvedValue(accounts);
    vi.mocked(api.listCategories).mockResolvedValue(categories);
    vi.mocked(api.listTransactions).mockResolvedValue(transactions);
    vi.mocked(api.getMonthlySummary).mockResolvedValue(summary);
    vi.mocked(preferencesApi.getPreferences).mockResolvedValue({
      base_currency: "EUR",
      locale: "es-ES",
      has_transactions: true,
    });
  });

  it("muestra el total del mes, el desglose por categoría y el listado de movimientos", async () => {
    renderPage();

    expect(await screen.findByText("Supermercado")).toBeInTheDocument();
    expect(screen.getAllByText("45,50 €").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Comida").length).toBeGreaterThan(0);
  });

  it("elimina un movimiento al hacer clic en Eliminar", async () => {
    const user = userEvent.setup();
    vi.mocked(api.deleteTransaction).mockResolvedValue(undefined);

    renderPage();

    await screen.findByText("Supermercado");
    await user.click(screen.getByRole("button", { name: "Eliminar" }));
    await user.click(screen.getByRole("button", { name: "Sí" }));

    await waitFor(() => expect(api.deleteTransaction).toHaveBeenCalledWith("test-token", 1));
  });

  it("agrega un movimiento nuevo desde el modal", async () => {
    const user = userEvent.setup();
    vi.mocked(api.createTransaction).mockResolvedValue(transactions.items[0]);

    renderPage();

    await screen.findByText("Supermercado");
    await user.click(screen.getByRole("button", { name: "+ Agregar movimiento" }));
    await user.type(screen.getByLabelText("Monto"), "10");
    await user.click(screen.getByRole("button", { name: "Agregar movimiento" }));

    await waitFor(() =>
      expect(api.createTransaction).toHaveBeenCalledWith(
        "test-token",
        expect.objectContaining({ account_id: 1, amount: "-10.00", direction: "expense" }),
      ),
    );
  });

  it("abre el modal de importar al hacer clic en el botón", async () => {
    const user = userEvent.setup();

    renderPage();

    await screen.findByText("Supermercado");
    await user.click(screen.getByRole("button", { name: "📥 Importar estado de cuenta" }));

    expect(await screen.findByRole("dialog", { name: "Importar estado de cuenta" })).toBeInTheDocument();
  });

  it("ofrece crear una cuenta cuando el usuario no tiene ninguna", async () => {
    vi.mocked(api.listAccounts).mockResolvedValue([]);

    renderPage();

    expect(await screen.findByText("Crea tu primera cuenta")).toBeInTheDocument();
  });

  it("muestra los formularios en línea (sin modal) cuando el usuario no tiene movimientos todavía", async () => {
    vi.mocked(api.listTransactions).mockResolvedValue({ items: [], next_cursor: null });
    vi.mocked(preferencesApi.getPreferences).mockResolvedValue({
      base_currency: "EUR",
      locale: "es-ES",
      has_transactions: false,
    });

    renderPage();

    expect(await screen.findByText("Importar estado de cuenta")).toBeInTheDocument();
    expect(screen.getByLabelText("Monto")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "+ Agregar movimiento" })).not.toBeInTheDocument();
  });
});
