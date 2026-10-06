import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Modal } from "../../components/Modal";
import { useAuth } from "../auth/useAuth";
import { MonthNavigator } from "../transactions/components/MonthNavigator";
import type { BudgetWithStatus } from "../transactions/types";
import { listBudgets } from "./api";
import { BudgetCard } from "./components/BudgetCard";
import { DeleteBudgetDialog, EditBudgetDialog } from "./components/BudgetDialogs";
import { BudgetForm } from "./components/BudgetForm";
import { CopyFromPrevious } from "./components/CopyFromPrevious";
import { RecommendationsView } from "./components/RecommendationsView";
import { currentYearMonth, isPastMonth } from "./period";

type EditableBudget = BudgetWithStatus & { category_id: number };
type View = "month" | "recommendations";

export function BudgetsPage() {
  const { token } = useAuth();
  const initial = currentYearMonth();
  const [year, setYear] = useState(initial.year);
  const [month, setMonth] = useState(initial.month);
  const [view, setView] = useState<View>("month");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editing, setEditing] = useState<EditableBudget | null>(null);
  const [deleting, setDeleting] = useState<EditableBudget | null>(null);

  const budgetsQuery = useQuery({
    queryKey: ["budgets", year, month],
    queryFn: () => listBudgets(token as string, year, month),
    enabled: token !== null,
  });

  const budgets = budgetsQuery.data ?? [];
  const hasBudgets = budgets.length > 0;
  const isPast = isPastMonth(year, month);

  return (
    <div className="budgets-page">
      <div className="budget-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={view === "month"}
          className={view === "month" ? "" : "button-secondary"}
          onClick={() => setView("month")}
        >
          Presupuestos del mes
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={view === "recommendations"}
          className={view === "recommendations" ? "" : "button-secondary"}
          onClick={() => setView("recommendations")}
        >
          Recomendaciones
        </button>
      </div>

      {view === "recommendations" ? (
        <RecommendationsView />
      ) : (
        <>
          <div className="expenses-toolbar">
            <MonthNavigator
              year={year}
              month={month}
              onChange={(newYear, newMonth) => {
                setYear(newYear);
                setMonth(newMonth);
              }}
            />

            {!isPast && (
              <div className="expenses-toolbar-actions">
                <CopyFromPrevious year={year} month={month} />
                {hasBudgets && (
                  <button type="button" onClick={() => setShowCreateModal(true)}>
                    + Nuevo presupuesto
                  </button>
                )}
              </div>
            )}
          </div>

          {isPast && (
            <p className="budget-note">
              Mes cerrado: los topes son de solo lectura. Lo gastado refleja tus movimientos
              actuales.
            </p>
          )}

          {!isPast && !budgetsQuery.isLoading && !hasBudgets && (
            <section>
              <h2>Nuevo presupuesto</h2>
              <BudgetForm year={year} month={month} />
            </section>
          )}

          <section className="budget-list">
            <h2>Presupuestos del mes</h2>
            {budgetsQuery.isLoading && <p className="page-status">Cargando presupuestos...</p>}
            {!budgetsQuery.isLoading && !hasBudgets && (
              <p className="page-status">No hay presupuestos para este mes.</p>
            )}
            {budgets.map((budget) => (
              <BudgetCard
                key={`${budget.category_id ?? "deleted"}-${budget.category_name}`}
                budget={budget}
                onEdit={() => budget.category_id !== null && setEditing(budget as EditableBudget)}
                onDelete={() =>
                  budget.category_id !== null && setDeleting(budget as EditableBudget)
                }
              />
            ))}
          </section>
        </>
      )}

      {showCreateModal && (
        <Modal title="Nuevo presupuesto" onClose={() => setShowCreateModal(false)}>
          <BudgetForm year={year} month={month} onCreated={() => setShowCreateModal(false)} />
        </Modal>
      )}
      {editing && <EditBudgetDialog budget={editing} onClose={() => setEditing(null)} />}
      {deleting && <DeleteBudgetDialog budget={deleting} onClose={() => setDeleting(null)} />}
    </div>
  );
}
