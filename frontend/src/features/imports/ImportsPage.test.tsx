import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as transactionsApi from "../transactions/api";
import type { Account, ImportPreview } from "../transactions/types";
import * as importsApi from "./api";
import { ImportsPage } from "./ImportsPage";

vi.mock("./api");
vi.mock("../transactions/api");
vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({ token: "test-token", user: { id: 1, email: "demo@example.com" } }),
}));

const accounts: Account[] = [
  {
    id: 5,
    owner_id: 1,
    name: "Cuenta Principal",
    type: "checking",
    currency: "EUR",
    initial_balance: "0.00",
    balance: "100.00",
    is_archived: false,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
];

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <ImportsPage />
    </QueryClientProvider>,
  );
}

describe("ImportsPage", () => {
  beforeEach(() => {
    vi.mocked(transactionsApi.listAccounts).mockResolvedValue(accounts);
    vi.mocked(importsApi.uploadStatement).mockReset();
    vi.mocked(importsApi.commitImport).mockReset();
  });

  it("sube un archivo y muestra la previsualización con conteos", async () => {
    const user = userEvent.setup();
    const preview: ImportPreview = {
      id: 42,
      account_id: 5,
      filename: "extracto.csv",
      status: "previewed",
      range_start: "2026-03-01",
      range_end: "2026-03-03",
      created_at: "2026-03-04T00:00:00Z",
      new_count: 1,
      exact_duplicate_count: 1,
      probable_duplicate_count: 0,
      rows: [
        {
          id: 1,
          posted_at: "2026-03-01",
          amount: "-42.50",
          raw_description: "COMPRA EN MERCADONA",
          classification: "NEW",
          matched_transaction_id: null,
        },
        {
          id: 2,
          posted_at: "2026-03-02",
          amount: "-10.00",
          raw_description: "PAGO EN BAR",
          classification: "EXACT_DUPLICATE",
          matched_transaction_id: 99,
        },
      ],
    };
    vi.mocked(importsApi.uploadStatement).mockResolvedValue(preview);

    renderPage();

    await waitFor(() => expect(screen.getByText("Cuenta Principal")).toBeInTheDocument());
    await user.selectOptions(screen.getByLabelText("Cuenta"), "5");

    const file = new File(["a,b\n1,2"], "extracto.csv", { type: "text/csv" });
    await user.upload(screen.getByLabelText("Archivo CSV"), file);

    await user.click(screen.getByRole("button", { name: "Previsualizar" }));

    expect(await screen.findByText(/extracto.csv/)).toBeInTheDocument();
    expect(screen.getByText("COMPRA EN MERCADONA")).toBeInTheDocument();
    expect(screen.getByText("PAGO EN BAR")).toBeInTheDocument();
    expect(importsApi.uploadStatement).toHaveBeenCalledWith("test-token", 5, file);
  });

  it("confirma la importación con la estrategia elegida", async () => {
    const user = userEvent.setup();
    const preview: ImportPreview = {
      id: 42,
      account_id: 5,
      filename: "extracto.csv",
      status: "previewed",
      range_start: "2026-03-01",
      range_end: "2026-03-01",
      created_at: "2026-03-04T00:00:00Z",
      new_count: 1,
      exact_duplicate_count: 0,
      probable_duplicate_count: 0,
      rows: [
        {
          id: 1,
          posted_at: "2026-03-01",
          amount: "-5.00",
          raw_description: "CAFE",
          classification: "NEW",
          matched_transaction_id: null,
        },
      ],
    };
    vi.mocked(importsApi.uploadStatement).mockResolvedValue(preview);
    vi.mocked(importsApi.commitImport).mockResolvedValue({
      id: 42,
      status: "committed",
      strategy: "append_new",
      inserted_count: 1,
      replaced_count: 0,
      skipped_count: 0,
    });

    renderPage();
    await waitFor(() => expect(screen.getByText("Cuenta Principal")).toBeInTheDocument());
    await user.selectOptions(screen.getByLabelText("Cuenta"), "5");
    const file = new File(["a,b\n1,2"], "extracto.csv", { type: "text/csv" });
    await user.upload(screen.getByLabelText("Archivo CSV"), file);
    await user.click(screen.getByRole("button", { name: "Previsualizar" }));
    await screen.findByText(/extracto.csv/);

    await user.click(screen.getByRole("button", { name: "Confirmar importación" }));

    expect(importsApi.commitImport).toHaveBeenCalledWith("test-token", 42, "append_new", []);
    expect(await screen.findByText(/1 insertados/)).toBeInTheDocument();
  });
});
