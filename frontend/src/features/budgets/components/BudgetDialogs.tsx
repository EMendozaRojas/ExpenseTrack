import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { Modal } from "../../../components/Modal";
import { useAuth } from "../../auth/useAuth";
import type { BudgetScope, BudgetWithStatus } from "../../transactions/types";
import { deleteBudget, updateBudget } from "../api";
import { formatPeriod } from "../period";
import { useInvalidateBudgets } from "../useInvalidateBudgets";
import { RecommendationHint } from "./RecommendationHint";
import { PlannedMonthsNote, ScopeChoice } from "./ScopeChoice";

interface DialogProps {
  budget: BudgetWithStatus & { category_id: number };
  onClose: () => void;
}

export function EditBudgetDialog({ budget, onClose }: DialogProps) {
  const { token } = useAuth();
  const invalidate = useInvalidateBudgets();
  const [amount, setAmount] = useState(budget.amount);
  const [repeat, setRepeat] = useState(budget.repeats);
  const [scope, setScope] = useState<BudgetScope>("this");
  const [error, setError] = useState<string | null>(null);

  // Solo se pregunta el alcance si el presupuesto se repite y sigue repitiéndose.
  const asksScope = budget.repeats && repeat;

  const mutation = useMutation({
    mutationFn: () =>
      updateBudget(token as string, budget.category_id, budget.month, {
        amount,
        scope: asksScope ? scope : "this",
        ...(repeat !== budget.repeats ? { repeat } : {}),
      }),
    onSuccess: () => {
      invalidate();
      onClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <Modal title="Editar presupuesto" onClose={onClose}>
      <div className="budget-form">
        <p>
          {budget.category_name} · {formatPeriod(budget.month)}
        </p>
        <div className="budget-form-grid">
          <label htmlFor="budget-edit-amount">Tope mensual</label>
          <input
            id="budget-edit-amount"
            type="number"
            min="0.01"
            step="0.01"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
          />
        </div>
        <RecommendationHint categoryId={budget.category_id} onUse={setAmount} />
        <label className="budget-checkbox">
          <input
            type="checkbox"
            checked={repeat}
            onChange={(event) => setRepeat(event.target.checked)}
          />
          Repetir cada mes
        </label>
        {budget.repeats && !repeat && (
          <p className="budget-note">
            Este mes se conserva y deja de repetirse a partir del siguiente.
          </p>
        )}
        {asksScope && <ScopeChoice value={scope} onChange={setScope} />}
        {asksScope && scope === "following" && (
          <PlannedMonthsNote categoryId={budget.category_id} period={budget.month} action="edit" />
        )}
        <button
          type="button"
          disabled={!amount || mutation.isPending}
          onClick={() => mutation.mutate()}
        >
          Guardar
        </button>
        {error && <p className="form-error">{error}</p>}
      </div>
    </Modal>
  );
}

export function DeleteBudgetDialog({ budget, onClose }: DialogProps) {
  const { token } = useAuth();
  const invalidate = useInvalidateBudgets();
  const [scope, setScope] = useState<BudgetScope>("this");
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => deleteBudget(token as string, budget.category_id, budget.month, scope),
    onSuccess: () => {
      invalidate();
      onClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <Modal title="Borrar presupuesto" onClose={onClose}>
      <div className="budget-form">
        <p>
          {budget.category_name} · {formatPeriod(budget.month)}
        </p>
        {budget.repeats ? (
          <>
            <ScopeChoice value={scope} onChange={setScope} />
            {scope === "following" && (
              <PlannedMonthsNote
                categoryId={budget.category_id}
                period={budget.month}
                action="delete"
              />
            )}
          </>
        ) : (
          <p className="budget-note">Se borrará el presupuesto de este mes.</p>
        )}
        <p className="budget-note">Los meses anteriores conservan su historial.</p>
        <button type="button" disabled={mutation.isPending} onClick={() => mutation.mutate()}>
          Borrar
        </button>
        {error && <p className="form-error">{error}</p>}
      </div>
    </Modal>
  );
}
