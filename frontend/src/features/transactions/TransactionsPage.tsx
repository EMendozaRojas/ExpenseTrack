import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { Modal } from "../../components/Modal";
import { useAuth } from "../auth/useAuth";
import { ImportsPage } from "../imports/ImportsPage";
import { getPreferences } from "../preferences/api";
import {
  createAccount,
  createCategory,
  createTransaction,
  deleteTransaction,
  getMonthlySummary,
  listAccounts,
  listCategories,
  listTransactions,
} from "./api";
import { CategoryBarChart } from "./components/CategoryBarChart";
import { MonthNavigator } from "./components/MonthNavigator";
import { StatTile } from "./components/StatTile";
import { TransactionForm } from "./components/TransactionForm";
import { TransactionList } from "./components/TransactionList";
import { formatCurrency, pad2 } from "./format";
import type { Account, Category, TransactionInput } from "./types";

const today = new Date();

function monthRange(year: number, month: number): { from: string; to: string } {
  const from = `${year}-${pad2(month)}-01`;
  const nextMonth = month === 12 ? 1 : month + 1;
  const nextYear = month === 12 ? year + 1 : year;
  const lastDay = new Date(nextYear, nextMonth - 1, 0).getDate();
  const to = `${year}-${pad2(month)}-${pad2(lastDay)}`;
  return { from, to };
}

export function TransactionsPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [newAccountName, setNewAccountName] = useState("");
  const [newAccountIsPrimary, setNewAccountIsPrimary] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);

  const { from: dateFrom, to: dateTo } = monthRange(year, month);

  const accountsQuery = useQuery({
    queryKey: ["accounts"],
    queryFn: () => listAccounts(token as string),
    enabled: token !== null,
  });

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: () => listCategories(token as string),
    enabled: token !== null,
  });

  const transactionsQuery = useQuery({
    queryKey: ["transactions", dateFrom, dateTo],
    queryFn: () => listTransactions(token as string, dateFrom, dateTo),
    enabled: token !== null,
  });

  const summaryQuery = useQuery({
    queryKey: ["summary", year, month],
    queryFn: () => getMonthlySummary(token as string, year, month),
    enabled: token !== null,
  });

  const preferencesQuery = useQuery({
    queryKey: ["preferences"],
    queryFn: () => getPreferences(token as string),
    enabled: token !== null,
  });

  const createAccountMutation = useMutation({
    mutationFn: (input: { name: string; isPrimary: boolean }) =>
      createAccount(token as string, {
        name: input.name,
        currency: "EUR",
        is_primary: input.isPrimary,
      }),
    onSuccess: (created: Account) => {
      queryClient.setQueryData<Account[]>(["accounts"], (previous) =>
        previous ? [...previous, created] : [created],
      );
    },
  });

  const createCategoryMutation = useMutation({
    mutationFn: (name: string) => createCategory(token as string, name),
    onSuccess: (created: Category) => {
      queryClient.setQueryData<Category[]>(["categories"], (previous) =>
        previous ? [...previous, created] : [created],
      );
    },
  });

  const createTransactionMutation = useMutation({
    mutationFn: (input: TransactionInput) => createTransaction(token as string, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["transactions", dateFrom, dateTo] });
      void queryClient.invalidateQueries({ queryKey: ["summary", year, month] });
      void queryClient.invalidateQueries({ queryKey: ["accounts"] });
      void queryClient.invalidateQueries({ queryKey: ["preferences"] });
      setShowAddModal(false);
    },
  });

  const deleteTransactionMutation = useMutation({
    mutationFn: (transactionId: number) => deleteTransaction(token as string, transactionId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["transactions", dateFrom, dateTo] });
      void queryClient.invalidateQueries({ queryKey: ["summary", year, month] });
      void queryClient.invalidateQueries({ queryKey: ["accounts"] });
    },
  });

  const categoriesById = useMemo(() => {
    const map = new Map<number, string>();
    for (const root of categoriesQuery.data ?? []) {
      map.set(root.id, root.name);
      for (const child of root.children) {
        map.set(child.id, `${root.name} · ${child.name}`);
      }
    }
    return map;
  }, [categoriesQuery.data]);

  const defaultDate = useMemo(() => {
    const isCurrentMonth = year === today.getFullYear() && month === today.getMonth() + 1;
    if (isCurrentMonth) {
      return `${today.getFullYear()}-${pad2(today.getMonth() + 1)}-${pad2(today.getDate())}`;
    }
    return `${year}-${pad2(month)}-01`;
  }, [year, month]);

  const accounts = accountsQuery.data ?? [];
  const hasAccounts = accounts.length > 0;
  const hasTransactionsEver = preferencesQuery.data?.has_transactions ?? false;

  const addMovementForm = (
    <TransactionForm
      accounts={accounts}
      categories={categoriesQuery.data ?? []}
      defaultDate={defaultDate}
      onSubmit={(input) => createTransactionMutation.mutate(input)}
      onCreateCategory={(name) => createCategoryMutation.mutateAsync(name)}
      isSubmitting={createTransactionMutation.isPending}
    />
  );

  return (
    <div className="expenses-page">
      <div className="expenses-toolbar">
        <MonthNavigator
          year={year}
          month={month}
          onChange={(newYear, newMonth) => {
            setYear(newYear);
            setMonth(newMonth);
          }}
        />

        {hasAccounts && hasTransactionsEver && (
          <div className="expenses-toolbar-actions">
            <button type="button" onClick={() => setShowAddModal(true)}>
              + Agregar movimiento
            </button>
            <button
              type="button"
              className="button-secondary"
              onClick={() => setShowImportModal(true)}
            >
              📥 Importar estado de cuenta
            </button>
          </div>
        )}
      </div>

      <section className="expenses-summary">
        <StatTile
          label="Total del mes"
          value={formatCurrency(Number(summaryQuery.data?.total ?? 0))}
        />
        {summaryQuery.isLoading ? (
          <p className="page-status">Cargando resumen...</p>
        ) : (
          <CategoryBarChart data={summaryQuery.data?.by_category ?? []} />
        )}
      </section>

      <section>
        <h2>Movimientos del mes</h2>
        {transactionsQuery.isLoading ? (
          <p className="page-status">Cargando movimientos...</p>
        ) : (
          <TransactionList
            transactions={transactionsQuery.data?.items ?? []}
            categoriesById={categoriesById}
            onDelete={(id) => deleteTransactionMutation.mutate(id)}
            isDeleting={deleteTransactionMutation.isPending}
          />
        )}
      </section>

      {!hasAccounts && !accountsQuery.isLoading && (
        <section>
          <div className="expense-form">
            <h2>Crea tu primera cuenta</h2>
            <p className="page-status">Necesitas al menos una cuenta para registrar movimientos.</p>
            <div className="expense-form-grid">
              <label htmlFor="new-account-name">Nombre</label>
              <input
                id="new-account-name"
                type="text"
                placeholder="Mi cuenta"
                value={newAccountName}
                onChange={(event) => setNewAccountName(event.target.value)}
              />
            </div>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={newAccountIsPrimary}
                onChange={(event) => setNewAccountIsPrimary(event.target.checked)}
              />
              Cuenta principal
            </label>
            <button
              type="button"
              disabled={!newAccountName.trim() || createAccountMutation.isPending}
              onClick={() => {
                createAccountMutation.mutate({
                  name: newAccountName.trim(),
                  isPrimary: newAccountIsPrimary,
                });
                setNewAccountName("");
              }}
            >
              Crear cuenta
            </button>
          </div>
        </section>
      )}

      {hasAccounts && !hasTransactionsEver && (
        <>
          <section>
            <h2>Agregar movimiento</h2>
            {addMovementForm}
          </section>
          <section>
            <h2>Importar estado de cuenta</h2>
            <ImportsPage />
          </section>
        </>
      )}

      {showAddModal && (
        <Modal title="Agregar movimiento" onClose={() => setShowAddModal(false)}>
          {addMovementForm}
        </Modal>
      )}

      {showImportModal && (
        <Modal title="Importar estado de cuenta" onClose={() => setShowImportModal(false)}>
          <ImportsPage />
        </Modal>
      )}
    </div>
  );
}
