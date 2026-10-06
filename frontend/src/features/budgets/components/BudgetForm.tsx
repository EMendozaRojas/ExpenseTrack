import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { useAuth } from "../../auth/useAuth";
import { listCategories } from "../../transactions/api";
import { flattenCategories } from "../../transactions/format";
import { createBudget } from "../api";
import { useInvalidateBudgets } from "../useInvalidateBudgets";
import { RecommendationHint } from "./RecommendationHint";

interface BudgetFormProps {
  year: number;
  month: number;
  onCreated?: () => void;
}

export function BudgetForm({ year, month, onCreated }: BudgetFormProps) {
  const { token } = useAuth();
  const invalidate = useInvalidateBudgets();
  const [categoryId, setCategoryId] = useState<number | "">("");
  const [amount, setAmount] = useState("");
  const [repeat, setRepeat] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);

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
    mutationFn: () =>
      createBudget(token as string, {
        category_id: categoryId as number,
        year,
        month,
        amount,
        repeat,
      }),
    onSuccess: () => {
      setCategoryId("");
      setAmount("");
      setRepeat(true);
      setFormError(null);
      invalidate();
      onCreated?.();
    },
    onError: (error: Error) => setFormError(error.message),
  });

  return (
    <div className="budget-form">
      <div className="budget-form-grid">
        <label htmlFor="budget-category">Categoría</label>
        <select
          id="budget-category"
          value={categoryId}
          onChange={(event) => setCategoryId(event.target.value ? Number(event.target.value) : "")}
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

      {categoryId !== "" && <RecommendationHint categoryId={categoryId} onUse={setAmount} />}

      <label className="budget-checkbox">
        <input
          type="checkbox"
          checked={repeat}
          onChange={(event) => setRepeat(event.target.checked)}
        />
        Repetir cada mes
      </label>

      <button
        type="button"
        disabled={!categoryId || !amount || createMutation.isPending}
        onClick={() => createMutation.mutate()}
      >
        Crear presupuesto
      </button>
      {formError && <p className="form-error">{formError}</p>}
    </div>
  );
}
