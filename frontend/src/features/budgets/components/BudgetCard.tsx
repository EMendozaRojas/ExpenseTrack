import { formatCurrency } from "../../transactions/format";
import type { BudgetWithStatus } from "../../transactions/types";

const STATUS_LABELS: Record<string, string> = {
  ok: "Dentro del presupuesto",
  warning: "Cerca del límite",
  exceeded: "Superado",
};

interface BudgetCardProps {
  budget: BudgetWithStatus;
  onEdit: () => void;
  onDelete: () => void;
}

export function BudgetCard({ budget, onEdit, onDelete }: BudgetCardProps) {
  const widthPercent = Math.min(budget.pct, 100);
  // Cada dato va en su propio elemento: el CSS los coloca en una fila en el
  // ordenador y de arriba abajo en el móvil (ver «Tarjeta de presupuesto»).
  return (
    <div className={`budget-card budget-card-${budget.status}`}>
      <div className="budget-card-header">
        <span className="budget-card-name">
          {budget.category_icon ? `${budget.category_icon} ` : ""}
          {budget.category_name}
          <span className="budget-card-badge">
            {budget.repeats ? "Se repite cada mes" : "Solo este mes"}
          </span>
        </span>
        <span className="budget-card-figures">
          <span className="budget-card-amounts">
            <span className="budget-card-spent">{formatCurrency(Number(budget.spent))}</span>
            <span className="budget-card-sep-desktop"> / </span>
            <span className="budget-card-sep-mobile"> de </span>
            {formatCurrency(Number(budget.amount))}
          </span>
          <span className={`budget-card-pct budget-card-status-${budget.status}`}>
            {budget.pct}%
          </span>
        </span>
      </div>
      <div className="budget-card-track">
        <div className="budget-card-bar" style={{ width: `${widthPercent}%` }} />
      </div>
      {budget.pace && (
        <p className={`budget-card-pace ${budget.pace.will_exceed ? "budget-card-pace-over" : ""}`}>
          A este ritmo acabarás el mes en {formatCurrency(Number(budget.pace.projected))}
        </p>
      )}
      <div className="budget-card-footer">
        <span className={`budget-card-status budget-card-status-${budget.status}`}>
          {STATUS_LABELS[budget.status]}
          <span className="budget-card-status-pct"> · {budget.pct}%</span>
        </span>
        {budget.editable && (
          <div className="budget-card-actions">
            <button type="button" className="button-secondary" onClick={onEdit}>
              Editar
            </button>
            <button type="button" className="button-secondary" onClick={onDelete}>
              Borrar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
