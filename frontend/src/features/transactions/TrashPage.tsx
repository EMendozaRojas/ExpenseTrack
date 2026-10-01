import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "../auth/useAuth";
import { listTrash, restoreTransaction } from "./api";
import { formatSignedCurrency } from "./format";

const MS_PER_DAY = 1000 * 60 * 60 * 24;

function daysRemaining(purgeAt: string): number {
  const diff = new Date(purgeAt).getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / MS_PER_DAY));
}

export function TrashPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  const trashQuery = useQuery({
    queryKey: ["transactions-trash"],
    queryFn: () => listTrash(token as string),
    enabled: token !== null,
  });

  const restoreMutation = useMutation({
    mutationFn: (transactionId: number) => restoreTransaction(token as string, transactionId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["transactions-trash"] });
      void queryClient.invalidateQueries({ queryKey: ["transactions"] });
      void queryClient.invalidateQueries({ queryKey: ["accounts"] });
    },
  });

  const items = trashQuery.data ?? [];

  return (
    <div className="trash-page">
      <h1>Papelera</h1>
      <p className="page-hint">
        Los movimientos borrados se conservan 30 días por si quieres recuperarlos. Pasado ese
        plazo se eliminan de forma definitiva, junto con sus adjuntos.
      </p>

      {trashQuery.isLoading && <p className="page-status">Cargando papelera...</p>}
      {!trashQuery.isLoading && items.length === 0 && (
        <p className="page-status">La papelera está vacía.</p>
      )}

      {items.map((item) => (
        <div key={item.id} className="trash-card">
          <div className="trash-card-info">
            <span className="trash-card-amount">{formatSignedCurrency(Number(item.amount))}</span>
            <span className="trash-card-note">{item.note || item.counterparty || "Sin nota"}</span>
            <span className="trash-card-date">{item.posted_at}</span>
          </div>
          <div className="trash-card-actions">
            <span className="trash-card-expiry">
              Se elimina en {daysRemaining(item.purge_at)} día(s)
            </span>
            <button
              type="button"
              disabled={restoreMutation.isPending}
              onClick={() => restoreMutation.mutate(item.id)}
            >
              Restaurar
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
