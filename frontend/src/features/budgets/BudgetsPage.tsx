import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { useAuth } from "../auth/useAuth";
import { listCategories } from "../transactions/api";
import { MonthNavigator } from "../transactions/components/MonthNavigator";
import { flattenCategories, formatCurrency } from "../transactions/format";
import type { BudgetWithStatus } from "../transactions/types";
import { createBudget, deleteBudget, listBudgets, updateBudget } from "./api";

const today = new Date();

const STATUS_LABELS: Record<string, string> = {
  ok: "Dentro del presupuesto",
  warning: "Cerca del límite",
  exceeded: "Superado",
};

export function BudgetsPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [categoryId, setCategoryId] = useState<number | "">("");
  const [amount, setAmount] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingAmount, setEditingAmount] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const budgetsQuery = useQuery({
    queryKey: ["budgets", year, month],
    queryFn: () => listBudgets(token as string, year, month),
    enabled: token !== null,
  });

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: () => listCategories(token as string),
    enabled: token !== null,
  });

  const expenseCategoryOptions = useMemo(() => {
    const expenseRoots = (categoriesQuery.data ?? []).filter((c) => c.kind === "expense");
    return flattenCategories(expenseRoots);
  }, [categoriesQuery.data]);

  const createMutation = useMutation({
    mutationFn: () => createBudget(token as string, { category_id: categoryId as number, amount }),
    onSuccess: () => {
      setCategoryId("");
      setAmount("");
      setFormError(null);
      void queryClient.invalidateQueries({ queryKey: ["budgets", year, month] });
    },
    onError: (error: Error) => setFormError(error.message),
  });

  const updateMutation = useMutation({
    mutationFn: (vars: { id: number; amount: string }) =>
      updateBudget(token as string, vars.id, { amount: vars.amount }),
    onSuccess: () => {
      setEditingId(null);
      void queryClient.invalidateQueries({ queryKey: ["budgets", year, month] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteBudget(token as string, id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["budgets", year, month] }),
  });

  const budgets = budgetsQuery.data ?? [];

  return (
    <div className="budgets-page">
      <MonthNavigator
        year={year}
        month={month}
        onChange={(newYear, newMonth) => {
          setYear(newYear);
          setMonth(newMonth);
        }}
      />

      <section className="budget-form">
        <h2>Nuevo presupuesto</h2>
        <div className="budget-form-grid">
          <label htmlFor="budget-category">Categoría</label>
          <select
            id="budget-category"
            value={categoryId}
            onChange={(event) =>
              setCategoryId(event.target.value ? Number(event.target.value) : "")
            }
          >
            <option value="">Selecciona una categoría de gasto</option>
            {expenseCategoryOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>

          <label htmlFor="budget-amount">Tope mensual</label>
          <input
            id="budget-amount"
            type="number"
            min="0.01"
            step="0.01"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
          />
        </div>
        <button
          type="button"
          disabled={!categoryId || !amount || createMutation.isPending}
          onClick={() => createMutation.mutate()}
        >
          Crear presupuesto
        </button>
        {formError && <p className="form-error">{formError}</p>}
      </section>

      <section className="budget-list">
        <h2>Presupuestos del mes</h2>
        {budgetsQuery.isLoading && <p className="page-status">Cargando presupuestos...</p>}
        {!budgetsQuery.isLoading && budgets.length === 0 && (
          <p className="page-status">Todavía no tienes presupuestos configurados.</p>
        )}
        {budgets.map((budget: BudgetWithStatus) => {
          const widthPercent = Math.min(budget.pct, 100);
          return (
            <div key={budget.id} className={`budget-card budget-card-${budget.status}`}>
              <div className="budget-card-header">
                <span className="budget-card-name">
                  {budget.category_icon ? `${budget.category_icon} ` : ""}
                  {budget.category_name}
                </span>
                <span className="budget-card-amounts">
                  {formatCurrency(Number(budget.spent))} / {formatCurrency(Number(budget.amount))}
                </span>
              </div>
              <div className="budget-card-track">
                <div className="budget-card-bar" style={{ width: `${widthPercent}%` }} />
              </div>
              <div className="budget-card-footer">
                <span className={`budget-card-status budget-card-status-${budget.status}`}>
                  {STATUS_LABELS[budget.status]} · {budget.pct}%
                </span>
                <div className="budget-card-actions">
                  {editingId === budget.id ? (
                    <>
                      <input
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={editingAmount}
                        onChange={(event) => setEditingAmount(event.target.value)}
                      />
                      <button
                        type="button"
                        onClick={() =>
                          updateMutation.mutate({ id: budget.id, amount: editingAmount })
                        }
                        disabled={updateMutation.isPending}
                      >
                        Guardar
                      </button>
                      <button
                        type="button"
                        className="button-secondary"
                        onClick={() => setEditingId(null)}
                      >
                        Cancelar
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        type="button"
                        className="button-secondary"
                        onClick={() => {
                          setEditingId(budget.id);
                          setEditingAmount(budget.amount);
                        }}
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        className="button-secondary"
                        onClick={() => deleteMutation.mutate(budget.id)}
                        disabled={deleteMutation.isPending}
                      >
                        Borrar
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </section>
    </div>
  );
}
