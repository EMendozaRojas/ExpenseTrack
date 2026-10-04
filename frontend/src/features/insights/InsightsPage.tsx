import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { useAuth } from "../auth/useAuth";
import { MonthNavigator } from "../transactions/components/MonthNavigator";
import { formatCurrency } from "../transactions/format";
import {
  dismissRecurringSeries,
  getInsightSettings,
  listAntSpending,
  listRecurringSeries,
  restoreRecurringSeries,
} from "./api";

const today = new Date();

export function InsightsPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [showDismissed, setShowDismissed] = useState(false);

  const recurringQuery = useQuery({
    queryKey: ["insights-recurring"],
    queryFn: () => listRecurringSeries(token as string),
    enabled: token !== null,
  });

  const antSpendingQuery = useQuery({
    queryKey: ["insights-ant-spending", year, month],
    queryFn: () => listAntSpending(token as string, year, month),
    enabled: token !== null,
  });

  const settingsQuery = useQuery({
    queryKey: ["insights-settings"],
    queryFn: () => getInsightSettings(token as string),
    enabled: token !== null,
  });

  const dismissMutation = useMutation({
    mutationFn: (seriesKey: string) => dismissRecurringSeries(token as string, seriesKey),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["insights-recurring"] }),
  });

  const restoreMutation = useMutation({
    mutationFn: (seriesKey: string) => restoreRecurringSeries(token as string, seriesKey),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["insights-recurring"] }),
  });

  const visibleSeries = useMemo(() => {
    const all = recurringQuery.data ?? [];
    return showDismissed ? all : all.filter((s) => !s.dismissed);
  }, [recurringQuery.data, showDismissed]);

  const settings = settingsQuery.data;

  return (
    <div className="insights-page">
      <h1>Análisis</h1>

      <section>
        <div className="insights-section-header">
          <h2>Pagos recurrentes</h2>
          <label className="insights-toggle">
            <input
              type="checkbox"
              checked={showDismissed}
              onChange={(event) => setShowDismissed(event.target.checked)}
            />
            Mostrar descartados
          </label>
        </div>
        <p className="page-status">Últimos 6 meses · se recalcula cada vez que entras.</p>

        {recurringQuery.isLoading && <p className="page-status">Buscando patrones...</p>}
        {!recurringQuery.isLoading && visibleSeries.length === 0 && (
          <p className="page-status">No se detectaron pagos recurrentes todavía.</p>
        )}
        <div className="recurring-list">
          {visibleSeries.map((series) => (
            <div key={series.key} className={`recurring-card ${series.dismissed ? "recurring-card-dismissed" : ""}`}>
              <div className="recurring-card-main">
                <span className="recurring-card-label">{series.label}</span>
                <span className="page-status">
                  {series.category_name ?? "Sin categoría"} · {series.cadence_label} ·{" "}
                  {series.occurrences} veces · última el {series.last_posted_at}
                </span>
              </div>
              <span className="recurring-card-amount">
                {series.direction === "expense" ? "-" : "+"}
                {formatCurrency(Number(series.avg_amount))}
              </span>
              {series.dismissed ? (
                <button
                  type="button"
                  className="button-secondary"
                  onClick={() => restoreMutation.mutate(series.key)}
                >
                  Restaurar
                </button>
              ) : (
                <button
                  type="button"
                  className="button-secondary"
                  onClick={() => dismissMutation.mutate(series.key)}
                >
                  Descartar
                </button>
              )}
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Gasto hormiga</h2>
        <MonthNavigator
          year={year}
          month={month}
          onChange={(newYear, newMonth) => {
            setYear(newYear);
            setMonth(newMonth);
          }}
        />
        {settings && (
          <p className="page-status">
            Movimientos de hasta {formatCurrency(Number(settings.ant_max_amount))}, con al menos{" "}
            {settings.ant_min_occurrences} ocurrencias y {formatCurrency(Number(settings.ant_min_aggregate))}{" "}
            acumulados en el mes.
          </p>
        )}

        {antSpendingQuery.isLoading && <p className="page-status">Calculando...</p>}
        {!antSpendingQuery.isLoading && (antSpendingQuery.data ?? []).length === 0 && (
          <p className="page-status">No hay gastos hormiga aún registrados.</p>
        )}
        {(antSpendingQuery.data ?? []).length > 0 && (
          <div className="ant-spending-list">
            {(antSpendingQuery.data ?? []).map((group) => (
              <div key={group.category_id} className="ant-spending-card">
                <span className="recurring-card-label">{group.category_name}</span>
                <span className="page-status">
                  {group.occurrences} movimientos · media {formatCurrency(Number(group.avg_amount))}
                </span>
                <span className="recurring-card-amount">{formatCurrency(Number(group.aggregate))}</span>
              </div>
            ))}
          </div>
        )}
        <p className="page-hint">
          Los umbrales de "gasto hormiga" se ajustan desde Configuración.
        </p>
      </section>
    </div>
  );
}
