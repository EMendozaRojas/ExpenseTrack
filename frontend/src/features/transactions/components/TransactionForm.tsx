import { useEffect, useMemo, useState, type FormEvent } from "react";

import { flattenCategories } from "../format";
import type { Account, Category, TransactionInput } from "../types";

const NEW_CATEGORY_VALUE = "__new__";
const NO_CATEGORY_VALUE = "__none__";

interface TransactionFormProps {
  accounts: Account[];
  categories: Category[];
  defaultDate: string;
  onSubmit: (input: TransactionInput) => void;
  onCreateCategory: (name: string) => Promise<Category>;
  isSubmitting: boolean;
}

export function TransactionForm({
  accounts,
  categories,
  defaultDate,
  onSubmit,
  onCreateCategory,
  isSubmitting,
}: TransactionFormProps) {
  const [accountId, setAccountId] = useState("");
  const [direction, setDirection] = useState<"income" | "expense">("expense");
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [date, setDate] = useState(defaultDate);
  const [categoryId, setCategoryId] = useState(NO_CATEGORY_VALUE);
  const [newCategoryName, setNewCategoryName] = useState("");
  const [isCreatingCategory, setIsCreatingCategory] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const categoryOptions = useMemo(() => flattenCategories(categories), [categories]);

  useEffect(() => {
    if (!accountId && accounts.length > 0) {
      setAccountId(String(accounts[0].id));
    }
  }, [accounts, accountId]);

  useEffect(() => {
    setDate(defaultDate);
  }, [defaultDate]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!accountId) {
      setError("Selecciona una cuenta.");
      return;
    }

    const numericAmount = Number(amount);
    if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
      setError("Ingresa un monto válido mayor a 0.");
      return;
    }

    let resolvedCategoryId: number | null = null;

    if (categoryId === NEW_CATEGORY_VALUE) {
      const trimmedName = newCategoryName.trim();
      if (!trimmedName) {
        setError("Ingresa un nombre para la nueva categoría.");
        return;
      }
      setIsCreatingCategory(true);
      try {
        const created = await onCreateCategory(trimmedName);
        resolvedCategoryId = created.id;
      } catch {
        setError("No se pudo crear la categoría.");
        setIsCreatingCategory(false);
        return;
      }
      setIsCreatingCategory(false);
    } else if (categoryId !== NO_CATEGORY_VALUE) {
      resolvedCategoryId = Number(categoryId);
    }

    const signedAmount = direction === "expense" ? -numericAmount : numericAmount;

    onSubmit({
      account_id: Number(accountId),
      amount: signedAmount.toFixed(2),
      direction,
      posted_at: date,
      category_id: resolvedCategoryId,
      note: note.trim() || null,
    });

    setAmount("");
    setNote("");
    setNewCategoryName("");
  }

  return (
    <form className="expense-form" onSubmit={handleSubmit}>
      <div className="expense-form-grid">
        {/* Con una sola cuenta no se pregunta: se usa esa (la elige el efecto de arriba). */}
        {accounts.length > 1 && (
          <>
            <label htmlFor="transaction-account">Cuenta</label>
            <select
              id="transaction-account"
              value={accountId}
              onChange={(event) => setAccountId(event.target.value)}
            >
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name}
                </option>
              ))}
            </select>
          </>
        )}

        <span id="transaction-direction-label">Tipo</span>
        <div role="radiogroup" aria-labelledby="transaction-direction-label">
          <label>
            <input
              type="radio"
              name="direction"
              value="expense"
              checked={direction === "expense"}
              onChange={() => setDirection("expense")}
            />
            Gasto
          </label>
          <label>
            <input
              type="radio"
              name="direction"
              value="income"
              checked={direction === "income"}
              onChange={() => setDirection("income")}
            />
            Ingreso
          </label>
        </div>

        <label htmlFor="expense-amount">Monto</label>
        <input
          id="expense-amount"
          type="number"
          step="0.01"
          required
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
        />

        <label htmlFor="expense-date">Fecha</label>
        <input
          id="expense-date"
          type="date"
          required
          value={date}
          onChange={(event) => setDate(event.target.value)}
        />

        <label htmlFor="expense-note">Descripción</label>
        <input
          id="expense-note"
          type="text"
          value={note}
          onChange={(event) => setNote(event.target.value)}
        />

        <label htmlFor="expense-category">Categoría</label>
        <select
          id="expense-category"
          value={categoryId}
          onChange={(event) => setCategoryId(event.target.value)}
        >
          <option value={NO_CATEGORY_VALUE}>Sin categoría</option>
          {categoryOptions.map((category) => (
            <option key={category.id} value={category.id}>
              {category.label}
            </option>
          ))}
          <option value={NEW_CATEGORY_VALUE}>+ Nueva categoría</option>
        </select>

        {categoryId === NEW_CATEGORY_VALUE && (
          <>
            <label htmlFor="new-category-name">Nombre de la categoría</label>
            <input
              id="new-category-name"
              type="text"
              value={newCategoryName}
              onChange={(event) => setNewCategoryName(event.target.value)}
            />
          </>
        )}
      </div>

      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}

      <button type="submit" disabled={isSubmitting || isCreatingCategory || !accountId}>
        {isSubmitting || isCreatingCategory ? "Guardando..." : "Agregar movimiento"}
      </button>
    </form>
  );
}
