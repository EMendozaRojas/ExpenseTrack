import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as transactionsApi from "../transactions/api";
import type { BudgetWithStatus, Category } from "../transactions/types";
import * as budgetsApi from "./api";
import { BudgetsPage } from "./BudgetsPage";

vi.mock("./api");
vi.mock("../transactions/api");
vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({ token: "test-token", user: { id: 1, email: "demo@example.com" } }),
}));

const categories: Category[] = [
  {
    id: 1,
    name: "Alimentación",
    owner_id: null,
    parent_id: null,
    kind: "expense",
    icon: "🛒",
    color: null,
    is_system: true,
    is_fixed: false,
    created_at: "2026-01-01T00:00:00Z",
    children: [
      {
        id: 2,
        name: "Supermercado",
        owner_id: null,
        parent_id: 1,
        kind: "expense",
        icon: null,
        color: null,
        is_system: true,
        is_fixed: false,
        created_at: "2026-01-01T00:00:00Z",
        children: [],
      },
    ],
  },
];

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <BudgetsPage />
    </QueryClientProvider>,
  );
}

describe("BudgetsPage", () => {
  beforeEach(() => {
    vi.mocked(transactionsApi.listCategories).mockResolvedValue(categories);
    vi.mocked(budgetsApi.createBudget).mockReset();
    vi.mocked(budgetsApi.deleteBudget).mockReset();
  });

  it("muestra los presupuestos existentes con su progreso y estado", async () => {
    const budgets: BudgetWithStatus[] = [
      {
        id: 1,
        category_id: 2,
        category_name: "Supermercado",
        category_icon: null,
        amount: "200.00",
        is_active: true,
        spent: "180.00",
        pct: 90,
        status: "warning",
      },
    ];
    vi.mocked(budgetsApi.listBudgets).mockResolvedValue(budgets);

    renderPage();

    expect(await screen.findByText("Supermercado")).toBeInTheDocument();
    expect(screen.getByText(/Cerca del límite/)).toBeInTheDocument();
  });

  it("crea un presupuesto nuevo con la categoría y el importe elegidos", async () => {
    const user = userEvent.setup();
    vi.mocked(budgetsApi.listBudgets).mockResolvedValue([]);
    vi.mocked(budgetsApi.createBudget).mockResolvedValue({
      id: 1,
      category_id: 2,
      category_name: "Supermercado",
      amount: "200.00",
      is_active: true,
      created_at: "2026-01-01T00:00:00Z",
    });

    renderPage();

    await waitFor(() =>
      expect(screen.getByText("Alimentación · Supermercado")).toBeInTheDocument(),
    );
    await user.selectOptions(screen.getByLabelText("Categoría"), "2");
    await user.type(screen.getByLabelText("Tope mensual"), "200");
    await user.click(screen.getByRole("button", { name: "Crear presupuesto" }));

    expect(budgetsApi.createBudget).toHaveBeenCalledWith("test-token", {
      category_id: 2,
      amount: "200",
    });
  });
});
