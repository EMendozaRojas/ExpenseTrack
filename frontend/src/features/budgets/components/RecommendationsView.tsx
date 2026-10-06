import { useMutation, useQuery } from "@tanstack/react-query";

import { useAuth } from "../../auth/useAuth";
import { formatCurrency } from "../../transactions/format";
import type { BudgetRecommendation, BudgetRecommendationFlag } from "../../transactions/types";
import { createBudget, listRecommendations, updateBudget } from "../api";
import { currentYearMonth, formatPeriod, toPeriod } from "../period";
import { useInvalidateBudgets } from "../useInvalidateBudgets";

const FLAG_LABELS: Record<BudgetRecommendationFlag, string> = {
  raise: "Subir el tope",
  lower: "Bajar el tope",
  keep: "Tope adecuado",
  create: "Sin presupuesto",
};

/** Vista aparte de recomendaciones de tope para el mes en curso. */
export function RecommendationsView() {
  const { token } = useAuth();
  const invalidate = useInvalidateBudgets();
  const { year, month } = currentYearMonth();

  const query = useQuery({
    queryKey: ["budget-recommendations", "all"],
    queryFn: () => listRecommendations(token as string),
    enabled: token !== null,
  });

  const mutation = useMutation({
    mutationFn: (recommendation: BudgetRecommendation) =>
      recommendation.flag === "create"
        ? createBudget(token as string, {
            category_id: recommendation.category_id,
            year,
            month,
            amount: recommendation.suggested_amount,
            repeat: true,
          })
        : updateBudget(token as string, recommendation.category_id, toPeriod(year, month), {
            amount: recommendation.suggested_amount,
            scope: "following",
          }),
    onSuccess: invalidate,
  });

  const recommendations = query.data ?? [];

  return (
    <section className="budget-list">
      <h2>Recomendaciones de tope</h2>
      <p className="page-status">
        Basadas en tu gasto de los últimos 3 meses completos. Se aplican desde{" "}
        {formatPeriod(toPeriod(year, month))} en adelante.
      </p>
      {query.isLoading && <p className="page-status">Cargando recomendaciones...</p>}
      {!query.isLoading && recommendations.length === 0 && (
        <p className="page-status">Todavía no hay historial suficiente para recomendar topes.</p>
      )}
      {recommendations.map((recommendation) => (
        <div key={recommendation.category_id} className="budget-card">
          <div className="budget-card-header">
            <span>{recommendation.category_name}</span>
            <span className="budget-card-badge">{FLAG_LABELS[recommendation.flag]}</span>
          </div>
          <p className="budget-hint-basis">
            {recommendation.basis.months
              .map((m) => `${formatPeriod(m.month)}: ${formatCurrency(Number(m.spent))}`)
              .join(" · ")}
            {" · "}media {formatCurrency(Number(recommendation.basis.mean))}
            {recommendation.basis.same_month_last_year !== null &&
              ` · mismo mes del año pasado: ${formatCurrency(
                Number(recommendation.basis.same_month_last_year),
              )}`}
          </p>
          {recommendation.basis.over_typical && (
            <p className="budget-note">
              Esta categoría supone el {recommendation.basis.share_pct}% de tu gasto, por encima de
              lo habitual.
            </p>
          )}
          <div className="budget-card-footer">
            <span>
              Sugerido: <strong>{formatCurrency(Number(recommendation.suggested_amount))}</strong>
              {recommendation.current_amount !== null &&
                ` (actual: ${formatCurrency(Number(recommendation.current_amount))})`}
            </span>
            {recommendation.flag !== "keep" && (
              <button
                type="button"
                className="button-secondary"
                disabled={mutation.isPending}
                onClick={() => mutation.mutate(recommendation)}
              >
                {recommendation.flag === "create" ? "Crear presupuesto" : "Aplicar sugerido"}
              </button>
            )}
          </div>
        </div>
      ))}
    </section>
  );
}
