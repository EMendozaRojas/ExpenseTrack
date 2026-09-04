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
          return (
            <tr key={transaction.id}>
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
              <td>
                {transaction.direction !== "transfer" && (
                  <button
                    type="button"
                    className="button-secondary"
                    disabled={isDeleting}
                    onClick={() => onDelete(transaction.id)}
                  >
                    Eliminar
                  </button>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
