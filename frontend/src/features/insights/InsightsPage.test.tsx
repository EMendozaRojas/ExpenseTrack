import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { AntSpendingGroup, InsightSettings, RecurringSeries } from "../transactions/types";
import * as insightsApi from "./api";
import { InsightsPage } from "./InsightsPage";

vi.mock("./api");
vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({ token: "test-token", user: { id: 1, email: "demo@example.com" } }),
}));

const series: RecurringSeries[] = [
  {
    key: "expense:NETFLIX",
    label: "NETFLIX",
    direction: "expense",
    category_id: 5,
    category_name: "Streaming",
    occurrences: 4,
    avg_amount: "12.99",
    cadence_days: 30,
    cadence_label: "mensual",
    first_posted_at: "2026-01-01",
    last_posted_at: "2026-04-01",
    dismissed: false,
  },
];

const antSpending: AntSpendingGroup[] = [
  {
    category_id: 3,
    category_name: "Cafeterías",
    occurrences: 9,
    aggregate: "31.50",
    avg_amount: "3.50",
  },
];

const settings: InsightSettings = {
  ant_max_amount: "10.00",
  ant_min_occurrences: 5,
  ant_min_aggregate: "30.00",
};

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <InsightsPage />
    </QueryClientProvider>,
  );
}

describe("InsightsPage", () => {
  beforeEach(() => {
    vi.mocked(insightsApi.listRecurringSeries).mockResolvedValue(series);
    vi.mocked(insightsApi.listAntSpending).mockResolvedValue(antSpending);
    vi.mocked(insightsApi.getInsightSettings).mockResolvedValue(settings);
    vi.mocked(insightsApi.dismissRecurringSeries).mockReset();
  });

  it("muestra series recurrentes y gasto hormiga", async () => {
    renderPage();

    expect(await screen.findByText("NETFLIX")).toBeInTheDocument();
    expect(screen.getByText(/mensual/)).toBeInTheDocument();
    expect(await screen.findByText("Cafeterías")).toBeInTheDocument();
    expect(screen.getByText(/9 movimientos/)).toBeInTheDocument();
  });

  it("descarta una serie recurrente al hacer click en Descartar", async () => {
    const user = userEvent.setup();
    vi.mocked(insightsApi.dismissRecurringSeries).mockResolvedValue(undefined);

    renderPage();
    await screen.findByText("NETFLIX");

    await user.click(screen.getByRole("button", { name: "Descartar" }));

    expect(insightsApi.dismissRecurringSeries).toHaveBeenCalledWith("test-token", "expense:NETFLIX");
  });
});
