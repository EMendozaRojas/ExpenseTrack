import { useQuery } from "@tanstack/react-query";

import { useAuth } from "../../auth/useAuth";
import { formatCurrency } from "../../transactions/format";
import type { BudgetScope } from "../../transactions/types";
import { listPlannedMonths } from "../api";
import { formatPeriod } from "../period";

interface ScopeChoiceProps {
  value: BudgetScope;
  onChange: (scope: BudgetScope) => void;
}

export function ScopeChoice({ value, onChange }: ScopeChoiceProps) {
  return (
    <fieldset className="budget-scope">
      <legend>¿A qué meses se aplica?</legend>
      <label className="budget-checkbox">
        <input
          type="radio"
          name="budget-scope"
          checked={value === "this"}
          onChange={() => onChange("this")}
        />
        Solo este mes
      </label>
      <label className="budget-checkbox">
        <input
          type="radio"
          name="budget-scope"
          checked={value === "following"}
          onChange={() => onChange("following")}
        />
        Este mes y los siguientes
      </label>
    </fieldset>
  );
}

interface PlannedMonthsNoteProps {
  categoryId: number;
  period: string;
  action: "edit" | "delete";
}

/** Meses posteriores con un monto propio: al editar se conservan, al borrar
 * "este mes y los siguientes" se borran también. */
export function PlannedMonthsNote({ categoryId, period, action }: PlannedMonthsNoteProps) {
  const { token } = useAuth();
  const query = useQuery({
    queryKey: ["budget-planned", categoryId, period],
    queryFn: () => listPlannedMonths(token as string, categoryId, period),
    enabled: token !== null,
  });

  const planned = query.data ?? [];
  if (planned.length === 0) return null;

  const list = planned
    .map((p) => `${formatPeriod(p.month)} (${formatCurrency(Number(p.amount))})`)
    .join(", ");
  return (
    <p className="budget-note" role="note">
      {action === "edit"
        ? `Estos meses tienen un monto propio y no se cambian: ${list}.`
        : `También se borrarán estos meses planificados: ${list}.`}
    </p>
  );
}
