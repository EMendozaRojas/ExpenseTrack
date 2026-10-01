import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { useAuth } from "../auth/useAuth";
import { getPreferences, updatePreferences } from "./api";
import { SUPPORTED_CURRENCIES } from "./currencies";

const CURRENCY_CHANGE_WARNING =
  "Este cambio afectará a tus nuevos registros. Tus datos pasados mantendrán el valor numérico con el que fueron guardados.";

export function PreferencesPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [selectedCurrency, setSelectedCurrency] = useState<string | null>(null);
  const [pendingCurrency, setPendingCurrency] = useState<string | null>(null);

  const preferencesQuery = useQuery({
    queryKey: ["preferences"],
    queryFn: () => getPreferences(token as string),
    enabled: token !== null,
  });

  useEffect(() => {
    if (preferencesQuery.data && selectedCurrency === null) {
      setSelectedCurrency(preferencesQuery.data.base_currency);
    }
  }, [preferencesQuery.data, selectedCurrency]);

  const mutation = useMutation({
    mutationFn: (currency: string) => updatePreferences(token as string, { base_currency: currency }),
    onSuccess: (updated) => {
      setSelectedCurrency(updated.base_currency);
      setPendingCurrency(null);
      void queryClient.invalidateQueries({ queryKey: ["preferences"] });
    },
  });

  const currentCurrency = preferencesQuery.data?.base_currency ?? null;

  function handleSelectChange(newCurrency: string) {
    setSelectedCurrency(newCurrency);
    if (currentCurrency && newCurrency !== currentCurrency) {
      setPendingCurrency(newCurrency);
    } else {
      setPendingCurrency(null);
    }
  }

  return (
    <div className="preferences-page">
      <h1>Configuración</h1>

      <section className="preferences-form">
        <h2>Moneda principal</h2>

        {preferencesQuery.isLoading && <p className="page-status">Cargando preferencias...</p>}

        {!preferencesQuery.isLoading && (
          <>
            <label htmlFor="preferences-base-currency">Moneda principal</label>
            <select
              id="preferences-base-currency"
              value={selectedCurrency ?? ""}
              onChange={(event) => handleSelectChange(event.target.value)}
            >
              {SUPPORTED_CURRENCIES.map((currency) => (
                <option key={currency} value={currency}>
                  {currency}
                </option>
              ))}
            </select>

            {pendingCurrency && (
              <div role="alert" className="preferences-warning">
                <p>{CURRENCY_CHANGE_WARNING}</p>
                <div className="preferences-warning-actions">
                  <button
                    type="button"
                    disabled={mutation.isPending}
                    onClick={() => mutation.mutate(pendingCurrency)}
                  >
                    Confirmar cambio
                  </button>
                  <button
                    type="button"
                    className="button-secondary"
                    onClick={() => {
                      setSelectedCurrency(currentCurrency);
                      setPendingCurrency(null);
                    }}
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            )}

            {!pendingCurrency && mutation.isSuccess && (
              <p className="page-status">Moneda principal actualizada.</p>
            )}
          </>
        )}
      </section>
    </div>
  );
}
