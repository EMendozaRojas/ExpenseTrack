import { useQuery } from "@tanstack/react-query";

import { useAuth } from "../../auth/useAuth";
import { formatCurrency } from "../../transactions/format";
import { listRecommendations } from "../api";
import { formatPeriod } from "../period";

interface RecommendationHintProps {
  categoryId: number;
  onUse: (amount: string) => void;
}

/** Tope sugerido para una categoría, con el cálculo visible, dentro de los
 * formularios de crear y editar. */
export function RecommendationHint({ categoryId, onUse }: RecommendationHintProps) {
  const { token } = useAuth();
  const query = useQuery({
    queryKey: ["budget-recommendations", categoryId],
    queryFn: () => listRecommendations(token as string, categoryId),
    enabled: token !== null,
  });

  const recommendation = query.data?.[0];
  if (!recommendation) return null;

  const months = recommendation.basis.months
    .map((m) => `${formatPeriod(m.month)}: ${formatCurrency(Number(m.spent))}`)
    .join(" · ");

  return (
    <div className="budget-hint">
      <span>
        Sugerido: <strong>{formatCurrency(Number(recommendation.suggested_amount))}</strong>
      </span>
      <span className="budget-hint-basis">
        Media de los últimos 3 meses ({months})
        {recommendation.basis.same_month_last_year !== null &&
          ` · mismo mes del año pasado: ${formatCurrency(
            Number(recommendation.basis.same_month_last_year),
          )}`}
      </span>
      <button
        type="button"
        className="button-secondary"
        onClick={() => onUse(recommendation.suggested_amount)}
      >
        Usar sugerido
      </button>
    </div>
  );
}
