import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Modal } from "../../../components/Modal";
import { useAuth } from "../../auth/useAuth";
import type { BudgetCopyPreviewItem } from "../../transactions/types";
import { copyBudgets, getCopyPreview } from "../api";
import { useInvalidateBudgets } from "../useInvalidateBudgets";

interface CopyFromPreviousProps {
  year: number;
  month: number;
}

/** Botón "Copiar del mes anterior": solo aparece si el mes anterior tiene
 * presupuestos que no se repiten y que aún no existen en este mes. */
export function CopyFromPrevious({ year, month }: CopyFromPreviousProps) {
  const { token } = useAuth();
  const [open, setOpen] = useState(false);

  const previewQuery = useQuery({
    queryKey: ["budget-copy-preview", year, month],
    queryFn: () => getCopyPreview(token as string, year, month),
    enabled: token !== null,
  });

  const items = previewQuery.data ?? [];
  if (items.length === 0) return null;

  return (
    <>
      <button type="button" className="button-secondary" onClick={() => setOpen(true)}>
        Copiar del mes anterior
      </button>
      {open && (
        <CopyDialog year={year} month={month} items={items} onClose={() => setOpen(false)} />
      )}
    </>
  );
}

interface CopyDialogProps extends CopyFromPreviousProps {
  items: BudgetCopyPreviewItem[];
  onClose: () => void;
}

function CopyDialog({ year, month, items, onClose }: CopyDialogProps) {
  const { token } = useAuth();
  const invalidate = useInvalidateBudgets();
  const [selected, setSelected] = useState<Record<number, boolean>>(
    Object.fromEntries(items.map((item) => [item.category_id, true])),
  );
  const [amounts, setAmounts] = useState<Record<number, string>>(
    Object.fromEntries(items.map((item) => [item.category_id, item.amount])),
  );
  const [error, setError] = useState<string | null>(null);

  const chosen = items.filter((item) => selected[item.category_id]);

  const mutation = useMutation({
    mutationFn: () =>
      copyBudgets(token as string, {
        year,
        month,
        items: chosen.map((item) => ({
          category_id: item.category_id,
          amount: amounts[item.category_id],
        })),
      }),
    onSuccess: () => {
      invalidate();
      onClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <Modal title="Copiar del mes anterior" onClose={onClose}>
      <div className="budget-form">
        <p className="budget-note">
          Presupuestos de un solo mes del mes anterior. Se crean como presupuestos de este mes.
        </p>
        {items.map((item) => (
          <div key={item.category_id} className="budget-copy-row">
            <label className="budget-checkbox">
              <input
                type="checkbox"
                checked={selected[item.category_id]}
                onChange={(event) =>
                  setSelected({ ...selected, [item.category_id]: event.target.checked })
                }
              />
              {item.category_name}
            </label>
            <input
              type="number"
              min="0.01"
              step="0.01"
              aria-label={`Monto de ${item.category_name}`}
              value={amounts[item.category_id]}
              onChange={(event) =>
                setAmounts({ ...amounts, [item.category_id]: event.target.value })
              }
            />
          </div>
        ))}
        <button
          type="button"
          disabled={chosen.length === 0 || mutation.isPending}
          onClick={() => mutation.mutate()}
        >
          Copiar {chosen.length} {chosen.length === 1 ? "presupuesto" : "presupuestos"}
        </button>
        {error && <p className="form-error">{error}</p>}
      </div>
    </Modal>
  );
}
