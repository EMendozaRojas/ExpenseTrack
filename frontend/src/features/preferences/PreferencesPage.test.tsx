import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as preferencesApi from "./api";
import { PreferencesPage } from "./PreferencesPage";

vi.mock("./api");
vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({ token: "test-token", user: { id: 1, email: "demo@example.com" } }),
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
  });

  it("muestra la moneda principal actual", async () => {
    vi.mocked(preferencesApi.getPreferences).mockResolvedValue({
      base_currency: "EUR",
      locale: "es-ES",
    });

    renderPreferencesPage();

    expect(await screen.findByLabelText("Moneda principal")).toHaveValue("EUR");
  });

  it("pide confirmación con el aviso antes de aplicar el cambio de moneda", async () => {
    const user = userEvent.setup();
    vi.mocked(preferencesApi.getPreferences).mockResolvedValue({
      base_currency: "EUR",
      locale: "es-ES",
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
    });
    vi.mocked(preferencesApi.updatePreferences).mockResolvedValue({
      base_currency: "USD",
      locale: "es-ES",
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
    });

    renderPreferencesPage();

    await user.selectOptions(await screen.findByLabelText("Moneda principal"), "USD");
    await user.click(await screen.findByRole("button", { name: "Cancelar" }));

    expect(preferencesApi.updatePreferences).not.toHaveBeenCalled();
    expect(await screen.findByLabelText("Moneda principal")).toHaveValue("EUR");
  });
});
