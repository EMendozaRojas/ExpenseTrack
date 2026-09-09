import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { SavingsGoal } from "../transactions/types";
import * as goalsApi from "./api";
import { GoalsPage } from "./GoalsPage";

vi.mock("./api");
vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({ token: "test-token", user: { id: 1, email: "demo@example.com" } }),
}));

const goals: SavingsGoal[] = [
  {
    id: 1,
    name: "Fondo de emergencia",
    target_amount: "3000.00",
    target_date: null,
    linked_account_id: null,
    status: "active",
    current_amount: "750.00",
    pct: 25,
    created_at: "2026-01-01T00:00:00Z",
  },
];

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <GoalsPage />
    </QueryClientProvider>,
  );
}

describe("GoalsPage", () => {
  beforeEach(() => {
    vi.mocked(goalsApi.listGoals).mockResolvedValue(goals);
    vi.mocked(goalsApi.createGoal).mockReset();
    vi.mocked(goalsApi.addContribution).mockReset();
    vi.mocked(goalsApi.getProjection).mockReset();
  });

  it("muestra las metas con su progreso", async () => {
    renderPage();

    expect(await screen.findByText("Fondo de emergencia")).toBeInTheDocument();
    expect(screen.getByText(/750,00/)).toBeInTheDocument();
  });

  it("crea una meta nueva con el formulario", async () => {
    const user = userEvent.setup();
    vi.mocked(goalsApi.createGoal).mockResolvedValue({
      id: 2,
      name: "Viaje",
      target_amount: "1500.00",
      target_date: null,
      linked_account_id: null,
      status: "active",
      current_amount: "0",
      pct: 0,
      created_at: "2026-01-01T00:00:00Z",
    });

    renderPage();
    await screen.findByText("Fondo de emergencia");

    await user.type(screen.getByLabelText("Nombre"), "Viaje");
    await user.type(screen.getByLabelText("Importe objetivo"), "1500");
    await user.click(screen.getByRole("button", { name: "Crear meta" }));

    expect(goalsApi.createGoal).toHaveBeenCalledWith("test-token", {
      name: "Viaje",
      target_amount: "1500",
      target_date: null,
    });
  });

  it("registra una aportación sobre una meta existente", async () => {
    const user = userEvent.setup();
    vi.mocked(goalsApi.addContribution).mockResolvedValue({
      id: 1,
      goal_id: 1,
      amount: "50.00",
      contributed_at: "2026-03-01",
      note: null,
      created_at: "2026-03-01T00:00:00Z",
    });

    renderPage();
    await screen.findByText("Fondo de emergencia");

    const [amountInput] = screen.getAllByPlaceholderText("Importe");
    await user.type(amountInput, "50");
    await user.click(screen.getByRole("button", { name: "Aportar" }));

    expect(goalsApi.addContribution).toHaveBeenCalledWith(
      "test-token",
      1,
      expect.objectContaining({ amount: "50" }),
    );
  });
});
