import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as transactionsApi from "../transactions/api";
import type { BudgetRecommendation, BudgetWithStatus, Category } from "../transactions/types";
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

function budget(overrides: Partial<BudgetWithStatus> = {}): BudgetWithStatus {
  return {
    category_id: 2,
    category_name: "Supermercado",
    category_icon: null,
    month: "2026-10",
    amount: "200.00",
    repeats: true,
    source: "series",
    editable: true,
    spent: "50.00",
    pct: 25,
    status: "ok",
    pace: null,
    ...overrides,
  };
}

const recommendation: BudgetRecommendation = {
  category_id: 2,
  category_name: "Supermercado",
  parent_id: 1,
  flag: "raise",
  suggested_amount: "320.00",
  current_amount: "200.00",
  basis: {
    months: [
      { month: "2026-07", spent: "300.00" },
      { month: "2026-08", spent: "320.00" },
      { month: "2026-09", spent: "340.00" },
    ],
    mean: "320.00",
    same_month_last_year: "410.00",
    share_pct: null,
    over_typical: null,
  },
};

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
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 9, 15));
    vi.mocked(transactionsApi.listCategories).mockResolvedValue(categories);
    vi.mocked(budgetsApi.listBudgets).mockReset();
    vi.mocked(budgetsApi.createBudget).mockReset();
    vi.mocked(budgetsApi.updateBudget).mockReset();
    vi.mocked(budgetsApi.deleteBudget).mockReset();
    vi.mocked(budgetsApi.getCopyPreview).mockResolvedValue([]);
    vi.mocked(budgetsApi.listPlannedMonths).mockResolvedValue([]);
    vi.mocked(budgetsApi.listRecommendations).mockResolvedValue([]);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("muestra los presupuestos con su progreso, estado, repetición y ritmo", async () => {
    vi.mocked(budgetsApi.listBudgets).mockResolvedValue([
      budget({
        spent: "180.00",
        pct: 90,
        status: "warning",
        pace: { projected: "360.00", will_exceed: true },
      }),
    ]);

    renderPage();

    expect(await screen.findByText("Supermercado")).toBeInTheDocument();
    expect(screen.getByText(/Cerca del límite/)).toBeInTheDocument();
    expect(screen.getByText("Se repite cada mes")).toBeInTheDocument();
    expect(screen.getByText(/A este ritmo acabarás el mes en 360,00/)).toBeInTheDocument();
  });

  it("oculta el formulario y lo abre en un modal desde el botón cuando ya hay presupuestos", async () => {
    const user = userEvent.setup();
    vi.mocked(budgetsApi.listBudgets).mockResolvedValue([budget()]);

    renderPage();

    await screen.findByText("Supermercado");
    expect(screen.queryByLabelText("Tope mensual")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "+ Nuevo presupuesto" }));

    expect(screen.getByRole("dialog", { name: "Nuevo presupuesto" })).toBeInTheDocument();
    expect(screen.getByLabelText("Tope mensual")).toBeInTheDocument();
  });

  it("crea un presupuesto que se repite usando el monto sugerido", async () => {
    const user = userEvent.setup();
    vi.mocked(budgetsApi.listBudgets).mockResolvedValue([]);
    vi.mocked(budgetsApi.listRecommendations).mockResolvedValue([recommendation]);
    vi.mocked(budgetsApi.createBudget).mockResolvedValue(budget());

    renderPage();

    await waitFor(() =>
      expect(screen.getByText("Alimentación · Supermercado")).toBeInTheDocument(),
    );
    expect(screen.getByLabelText("Repetir cada mes")).toBeChecked();
    await user.selectOptions(screen.getByLabelText("Categoría"), "2");
    expect(await screen.findByText(/mismo mes del año pasado/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Usar sugerido" }));
    await user.click(screen.getByRole("button", { name: "Crear presupuesto" }));

    expect(budgetsApi.createBudget).toHaveBeenCalledWith("test-token", {
      category_id: 2,
      year: 2026,
      month: 10,
      amount: "320.00",
      repeat: true,
    });
  });

  it("muestra el formulario en un mes futuro sin presupuestos", async () => {
    const user = userEvent.setup();
    vi.mocked(budgetsApi.listBudgets).mockImplementation(async (_token, _year, month) =>
      month === 10 ? [budget()] : [],
    );

    renderPage();
    await screen.findByText("Supermercado");

    await user.click(screen.getByRole("button", { name: /siguiente/i }));

    expect(await screen.findByLabelText("Tope mensual")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "+ Nuevo presupuesto" })).not.toBeInTheDocument();
  });

  it("los meses pasados son de solo lectura", async () => {
    const user = userEvent.setup();
    vi.mocked(budgetsApi.listBudgets).mockImplementation(async (_token, _year, month) =>
      month === 9 ? [budget({ month: "2026-09", editable: false })] : [],
    );

    renderPage();
    await user.click(screen.getByRole("button", { name: /anterior/i }));

    expect(await screen.findByText("Supermercado")).toBeInTheDocument();
    expect(screen.getByText(/Mes cerrado/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Editar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "+ Nuevo presupuesto" })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Tope mensual")).not.toBeInTheDocument();
  });

  it("edita este mes y los siguientes avisando de los meses planificados", async () => {
    const user = userEvent.setup();
    vi.mocked(budgetsApi.listBudgets).mockResolvedValue([budget()]);
    vi.mocked(budgetsApi.listPlannedMonths).mockResolvedValue([
      { month: "2026-12", amount: "600.00", kind: "override" },
    ]);
    vi.mocked(budgetsApi.updateBudget).mockResolvedValue(budget());

    renderPage();
    await user.click(await screen.findByRole("button", { name: "Editar" }));
    const dialog = screen.getByRole("dialog", { name: "Editar presupuesto" });
    const amount = within(dialog).getByLabelText("Tope mensual");
    await user.clear(amount);
    await user.type(amount, "300");
    await user.click(within(dialog).getByLabelText("Este mes y los siguientes"));

    expect(await within(dialog).findByText(/diciembre de 2026/)).toBeInTheDocument();
    await user.click(within(dialog).getByRole("button", { name: "Guardar" }));

    expect(budgetsApi.updateBudget).toHaveBeenCalledWith("test-token", 2, "2026-10", {
      amount: "300",
      scope: "following",
    });
  });

  it("deja de repetir un presupuesto sin preguntar el alcance", async () => {
    const user = userEvent.setup();
    vi.mocked(budgetsApi.listBudgets).mockResolvedValue([budget()]);
    vi.mocked(budgetsApi.updateBudget).mockResolvedValue(budget());

    renderPage();
    await user.click(await screen.findByRole("button", { name: "Editar" }));
    const dialog = screen.getByRole("dialog", { name: "Editar presupuesto" });
    await user.click(within(dialog).getByLabelText("Repetir cada mes"));

    expect(within(dialog).queryByLabelText("Solo este mes")).not.toBeInTheDocument();
    await user.click(within(dialog).getByRole("button", { name: "Guardar" }));

    expect(budgetsApi.updateBudget).toHaveBeenCalledWith("test-token", 2, "2026-10", {
      amount: "200.00",
      scope: "this",
      repeat: false,
    });
  });

  it("borra solo este mes de un presupuesto que se repite", async () => {
    const user = userEvent.setup();
    vi.mocked(budgetsApi.listBudgets).mockResolvedValue([budget()]);
    vi.mocked(budgetsApi.deleteBudget).mockResolvedValue(undefined);

    renderPage();
    await user.click(await screen.findByRole("button", { name: "Borrar" }));
    const dialog = screen.getByRole("dialog", { name: "Borrar presupuesto" });
    expect(within(dialog).getByLabelText("Solo este mes")).toBeChecked();
    await user.click(within(dialog).getByRole("button", { name: "Borrar" }));

    expect(budgetsApi.deleteBudget).toHaveBeenCalledWith("test-token", 2, "2026-10", "this");
  });

  it("copia presupuestos del mes anterior ajustando montos", async () => {
    const user = userEvent.setup();
    vi.mocked(budgetsApi.listBudgets).mockResolvedValue([budget()]);
    vi.mocked(budgetsApi.getCopyPreview).mockResolvedValue([
      { category_id: 7, category_name: "Ocio", amount: "150.00" },
      { category_id: 8, category_name: "Ropa", amount: "100.00" },
    ]);
    vi.mocked(budgetsApi.copyBudgets).mockResolvedValue({ created: [8], skipped: [] });

    renderPage();
    await user.click(await screen.findByRole("button", { name: "Copiar del mes anterior" }));
    const dialog = screen.getByRole("dialog", { name: "Copiar del mes anterior" });
    await user.click(within(dialog).getByLabelText("Ocio"));
    const ropa = within(dialog).getByLabelText("Monto de Ropa");
    await user.clear(ropa);
    await user.type(ropa, "200");
    await user.click(within(dialog).getByRole("button", { name: "Copiar 1 presupuesto" }));

    expect(budgetsApi.copyBudgets).toHaveBeenCalledWith("test-token", {
      year: 2026,
      month: 10,
      items: [{ category_id: 8, amount: "200" }],
    });
  });

  it("muestra las recomendaciones y aplica la sugerida desde este mes", async () => {
    const user = userEvent.setup();
    vi.mocked(budgetsApi.listBudgets).mockResolvedValue([]);
    vi.mocked(budgetsApi.listRecommendations).mockResolvedValue([
      recommendation,
      {
        ...recommendation,
        category_id: 1,
        category_name: "Alimentación",
        flag: "create",
        current_amount: null,
      },
    ]);
    vi.mocked(budgetsApi.updateBudget).mockResolvedValue(budget());
    vi.mocked(budgetsApi.createBudget).mockResolvedValue(budget());

    renderPage();
    await user.click(screen.getByRole("tab", { name: "Recomendaciones" }));

    expect(await screen.findByText("Subir el tope")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Aplicar sugerido" }));
    expect(budgetsApi.updateBudget).toHaveBeenCalledWith("test-token", 2, "2026-10", {
      amount: "320.00",
      scope: "following",
    });

    await user.click(screen.getByRole("button", { name: "Crear presupuesto" }));
    expect(budgetsApi.createBudget).toHaveBeenCalledWith("test-token", {
      category_id: 1,
      year: 2026,
      month: 10,
      amount: "320.00",
      repeat: true,
    });
  });
});
