import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { TrashedTransaction } from "./types";
import * as transactionsApi from "./api";
import { TrashPage } from "./TrashPage";

vi.mock("./api");
vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({ token: "test-token", user: { id: 1, email: "demo@example.com" } }),
}));

function renderTrashPage() {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <TrashPage />
    </QueryClientProvider>,
  );
}

function makeTrashedTransaction(overrides: Partial<TrashedTransaction> = {}): TrashedTransaction {
  const now = new Date();
  const purgeAt = new Date(now.getTime() + 15 * 24 * 60 * 60 * 1000);
  return {
    id: 1,
    account_id: 1,
    owner_id: 1,
    amount: "-15.50",
    direction: "expense",
    posted_at: "2026-09-01",
    category_id: null,
    counterparty: null,
    raw_description: null,
    note: "Café",
    source: "manual",
    transfer_group_id: null,
    created_at: now.toISOString(),
    updated_at: now.toISOString(),
    deleted_at: now.toISOString(),
    purge_at: purgeAt.toISOString(),
    ...overrides,
  };
}

describe("TrashPage", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("muestra un mensaje cuando la papelera está vacía", async () => {
    vi.mocked(transactionsApi.listTrash).mockResolvedValue([]);

    renderTrashPage();

    expect(await screen.findByText("La papelera está vacía.")).toBeInTheDocument();
  });

  it("lista movimientos borrados con los días restantes antes del borrado definitivo", async () => {
    vi.mocked(transactionsApi.listTrash).mockResolvedValue([makeTrashedTransaction()]);

    renderTrashPage();

    expect(await screen.findByText("Café")).toBeInTheDocument();
    expect(screen.getByText(/Se elimina en 15 día\(s\)/)).toBeInTheDocument();
  });

  it("restaura un movimiento al pulsar el botón", async () => {
    const user = userEvent.setup();
    vi.mocked(transactionsApi.listTrash).mockResolvedValue([makeTrashedTransaction()]);
    vi.mocked(transactionsApi.restoreTransaction).mockResolvedValue({
      id: 1,
      account_id: 1,
      owner_id: 1,
      amount: "-15.50",
      direction: "expense",
      posted_at: "2026-09-01",
      category_id: null,
      counterparty: null,
      raw_description: null,
      note: "Café",
      source: "manual",
      transfer_group_id: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    renderTrashPage();

    await user.click(await screen.findByRole("button", { name: "Restaurar" }));

    expect(transactionsApi.restoreTransaction).toHaveBeenCalledWith("test-token", 1);
  });
});
