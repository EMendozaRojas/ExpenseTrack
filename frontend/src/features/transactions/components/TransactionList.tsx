import { Fragment, useState } from "react";

import { AttachmentsPanel } from "../../attachments/AttachmentsPanel";
import { formatSignedCurrency } from "../format";
import type { Transaction } from "../types";

interface TransactionListProps {
  transactions: Transaction[];
  categoriesById: Map<number, string>;
  onDelete: (transactionId: number) => void;
  isDeleting: boolean;
}

export function TransactionList({
  transactions,
  categoriesById,
  onDelete,
  isDeleting,
}: TransactionListProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);

  if (transactions.length === 0) {
    return <p className="page-status">No hay movimientos registrados este mes.</p>;
  }

  return (
    <table className="expense-table">
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Descripción</th>
          <th>Categoría</th>
          <th>Monto</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {transactions.map((transaction) => {
          const amount = Number(transaction.amount);
          const sign = amount < 0 ? "expense" : "income";
          const isExpanded = expandedId === transaction.id;
          return (
            <Fragment key={transaction.id}>
              <tr>
                <td>{transaction.posted_at}</td>
                <td>{transaction.note ?? transaction.raw_description ?? "—"}</td>
                <td>
                  {transaction.category_id !== null
                    ? (categoriesById.get(transaction.category_id) ?? "—")
                    : "Sin categoría"}
                </td>
                <td className={`expense-table-amount expense-table-amount--${sign}`}>
                  {amount < 0 ? "-" : "+"}
                  {formatSignedCurrency(amount)}
                </td>
                <td className="expense-table-actions">
                  <button
                    type="button"
                    className="button-secondary"
                    onClick={() => setExpandedId(isExpanded ? null : transaction.id)}
                  >
                    {isExpanded ? "Ocultar adjuntos" : "Adjuntos"}
                  </button>
                  {transaction.direction !== "transfer" &&
                    (confirmDeleteId === transaction.id ? (
                      <span className="confirm-delete">
                        <span className="confirm-delete-text">¿Eliminar?</span>
                        <button
                          type="button"
                          disabled={isDeleting}
                          onClick={() => {
                            onDelete(transaction.id);
                            setConfirmDeleteId(null);
                          }}
                        >
                          Sí
                        </button>
                        <button
                          type="button"
                          className="button-secondary"
                          onClick={() => setConfirmDeleteId(null)}
                        >
                          No
                        </button>
                      </span>
                    ) : (
                      <button
                        type="button"
                        className="button-secondary"
                        disabled={isDeleting}
                        onClick={() => setConfirmDeleteId(transaction.id)}
                      >
                        Eliminar
                      </button>
                    ))}
                </td>
              </tr>
              {isExpanded && (
                <tr>
                  <td colSpan={5}>
                    <AttachmentsPanel transactionId={transaction.id} />
                  </td>
                </tr>
              )}
            </Fragment>
          );
        })}
      </tbody>
    </table>
  );
}
