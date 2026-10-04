import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as insightsApi from "../insights/api";
import * as profileApi from "../profile/api";
import * as preferencesApi from "./api";
import { PreferencesPage } from "./PreferencesPage";

vi.mock("./api");
vi.mock("../profile/api");
vi.mock("../insights/api");
vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({
    token: "test-token",
    user: { id: 1, email: "demo@example.com", full_name: "Demo User", has_avatar: false },
    refreshUser: vi.fn(),
  }),
}));

function renderPreferencesPage() {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <PreferencesPage />
    </QueryClientProvider>,
  );
}

describe("PreferencesPage", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(insightsApi.getInsightSettings).mockResolvedValue({
      ant_max_amount: "10.00",
      ant_min_occurrences: 5,
      ant_min_aggregate: "30.00",
    });
  });

  it("muestra la moneda principal actual", async () => {
    vi.mocked(preferencesApi.getPreferences).mockResolvedValue({
      base_currency: "EUR",
      locale: "es-ES",
      has_transactions: false,
    });

    renderPreferencesPage();

    expect(await screen.findByLabelText("Moneda principal")).toHaveValue("EUR");
  });

  it("pide confirmación con el aviso antes de aplicar el cambio de moneda", async () => {
    const user = userEvent.setup();
    vi.mocked(preferencesApi.getPreferences).mockResolvedValue({
      base_currency: "EUR",
      locale: "es-ES",
      has_transactions: false,
    });

    renderPreferencesPage();

    await user.selectOptions(await screen.findByLabelText("Moneda principal"), "USD");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Este cambio afectará a tus nuevos registros. Tus datos pasados mantendrán el valor numérico con el que fueron guardados.",
    );
    expect(preferencesApi.updatePreferences).not.toHaveBeenCalled();
  });

  it("aplica el cambio de moneda solo tras confirmar", async () => {
    const user = userEvent.setup();
    vi.mocked(preferencesApi.getPreferences).mockResolvedValue({
      base_currency: "EUR",
      locale: "es-ES",
      has_transactions: false,
    });
    vi.mocked(preferencesApi.updatePreferences).mockResolvedValue({
      base_currency: "USD",
      locale: "es-ES",
      has_transactions: false,
    });

    renderPreferencesPage();

    await user.selectOptions(await screen.findByLabelText("Moneda principal"), "USD");
    await user.click(await screen.findByRole("button", { name: "Confirmar cambio" }));

    expect(preferencesApi.updatePreferences).toHaveBeenCalledWith("test-token", {
      base_currency: "USD",
    });
    expect(await screen.findByText("Moneda principal actualizada.")).toBeInTheDocument();
  });

  it("cancelar descarta el cambio sin llamar a la API", async () => {
    const user = userEvent.setup();
    vi.mocked(preferencesApi.getPreferences).mockResolvedValue({
      base_currency: "EUR",
      locale: "es-ES",
      has_transactions: false,
    });

    renderPreferencesPage();

    await user.selectOptions(await screen.findByLabelText("Moneda principal"), "USD");
    await user.click(await screen.findByRole("button", { name: "Cancelar" }));

    expect(preferencesApi.updatePreferences).not.toHaveBeenCalled();
    expect(await screen.findByLabelText("Moneda principal")).toHaveValue("EUR");
  });

  it("permite editar el nombre completo", async () => {
    const user = userEvent.setup();
    vi.mocked(preferencesApi.getPreferences).mockResolvedValue({
      base_currency: "EUR",
      locale: "es-ES",
      has_transactions: false,
    });
    vi.mocked(profileApi.updateProfile).mockResolvedValue({
      id: 1,
      email: "demo@example.com",
      full_name: "Nuevo Nombre",
      has_avatar: false,
      created_at: "2026-01-01T00:00:00Z",
    });

    renderPreferencesPage();

    const nameInput = await screen.findByLabelText("Nombre completo");
    await user.clear(nameInput);
    await user.type(nameInput, "Nuevo Nombre");
    await user.click(screen.getByRole("button", { name: "Guardar nombre" }));

    expect(profileApi.updateProfile).toHaveBeenCalledWith("test-token", "Nuevo Nombre");
    expect(await screen.findByText("Nombre actualizado.")).toBeInTheDocument();
  });

  it("bloquea el selector de moneda cuando el usuario ya tiene movimientos", async () => {
    vi.mocked(preferencesApi.getPreferences).mockResolvedValue({
      base_currency: "EUR",
      locale: "es-ES",
      has_transactions: true,
    });

    renderPreferencesPage();

    expect(await screen.findByLabelText("Moneda principal")).toBeDisabled();
    expect(
      screen.getByText(
        "Ya tienes movimientos registrados, así que la moneda principal no se puede cambiar.",
      ),
    ).toBeInTheDocument();
  });

  it("permite editar los umbrales de gasto hormiga", async () => {
    const user = userEvent.setup();
    vi.mocked(preferencesApi.getPreferences).mockResolvedValue({
      base_currency: "EUR",
      locale: "es-ES",
      has_transactions: false,
    });
    vi.mocked(insightsApi.getInsightSettings).mockResolvedValue({
      ant_max_amount: "10.00",
      ant_min_occurrences: 5,
      ant_min_aggregate: "30.00",
    });
    vi.mocked(insightsApi.updateInsightSettings).mockResolvedValue({
      ant_max_amount: "15.00",
      ant_min_occurrences: 5,
      ant_min_aggregate: "30.00",
    });

    renderPreferencesPage();

    const maxAmountInput = await screen.findByLabelText("Importe máximo por movimiento");
    await user.clear(maxAmountInput);
    await user.type(maxAmountInput, "15.00");
    await user.click(screen.getByRole("button", { name: "Guardar umbrales" }));

    expect(insightsApi.updateInsightSettings).toHaveBeenCalledWith("test-token", {
      ant_max_amount: "15",
      ant_min_occurrences: 5,
      ant_min_aggregate: "30.00",
    });
    expect(await screen.findByText("Umbrales actualizados.")).toBeInTheDocument();
  });
});
