import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as api from "../transactions/api";
import type { DashboardSummary } from "../transactions/types";
import { DashboardPage } from "./DashboardPage";

vi.mock("../transactions/api");
vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({ token: "test-token", user: { id: 1, email: "demo@example.com" } }),
}));

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <DashboardPage />
    </QueryClientProvider>,
  );
}

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.mocked(api.getDashboardSummary).mockReset();
  });

  it("muestra entradas, salidas, saldo neto y desglose por categoría", async () => {
    const summary: DashboardSummary = {
      year: 2026,
      month: 9,
      income_total: "1000.00",
      expense_total: "400.00",
      net_total: "600.00",
      net_status: "a_favor",
      fixed_total: "300.00",
      variable_total: "100.00",
      by_category: [
        {
          category_id: 1,
          category_name: "Alimentación",
          icon: "🛒",
          color: "#4F86C6",
          total: "50.00",
          subcategories: [{ category_id: 11, category_name: "Supermercado", total: "50.00" }],
        },
      ],
      incomplete_data: false,
      last_transaction_date: "2026-09-08",
    };
    vi.mocked(api.getDashboardSummary).mockResolvedValue(summary);

    renderPage();

    expect(await screen.findByText(/1\.?000,00\s*€/)).toBeInTheDocument();
    expect(screen.getByText(/^400,00\s*€$/)).toBeInTheDocument();
    expect(screen.getByText(/A favor/)).toBeInTheDocument();
    expect(screen.getByText("Alimentación", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("Supermercado")).toBeInTheDocument();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("muestra el aviso de datos incompletos cuando corresponde", async () => {
    const summary: DashboardSummary = {
      year: 2026,
      month: 9,
      income_total: "0",
      expense_total: "0",
      net_total: "0",
      net_status: "en_contra",
      fixed_total: "0",
      variable_total: "0",
      by_category: [],
      incomplete_data: true,
      last_transaction_date: null,
    };
    vi.mocked(api.getDashboardSummary).mockResolvedValue(summary);

    renderPage();

    expect(await screen.findByRole("status")).toHaveTextContent("Datos incompletos");
    expect(screen.getByText(/En contra/)).toBeInTheDocument();
  });
});
