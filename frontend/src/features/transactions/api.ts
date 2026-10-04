import { apiFetch } from "../../api/client";
import type {
  Account,
  AccountInput,
  Category,
  DashboardSummary,
  MonthlySummary,
  Transaction,
  TransactionInput,
  TransactionPage,
} from "./types";

export function listCategories(token: string): Promise<Category[]> {
  return apiFetch<Category[]>("/categories/", token);
}

export function createCategory(token: string, name: string): Promise<Category> {
  return apiFetch<Category>("/categories/", token, {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function listAccounts(token: string): Promise<Account[]> {
  return apiFetch<Account[]>("/accounts/", token);
}

export function createAccount(token: string, payload: AccountInput): Promise<Account> {
  return apiFetch<Account>("/accounts/", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listTransactions(
  token: string,
  dateFrom: string,
  dateTo: string,
): Promise<TransactionPage> {
  return apiFetch<TransactionPage>(
    `/transactions/?date_from=${dateFrom}&date_to=${dateTo}&limit=200`,
    token,
  );
}

export function createTransaction(
  token: string,
  payload: TransactionInput,
): Promise<Transaction> {
  return apiFetch<Transaction>("/transactions/", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteTransaction(token: string, transactionId: number): Promise<void> {
  return apiFetch<void>(`/transactions/${transactionId}`, token, { method: "DELETE" });
}

export function getMonthlySummary(
  token: string,
  year: number,
  month: number,
): Promise<MonthlySummary> {
  return apiFetch<MonthlySummary>(`/expenses/summary?year=${year}&month=${month}`, token);
}

export function getDashboardSummary(
  token: string,
  year: number,
  month: number,
  accountId?: number | null,
): Promise<DashboardSummary> {
  const accountParam = accountId ? `&account_id=${accountId}` : "";
  return apiFetch<DashboardSummary>(
    `/dashboard/summary?year=${year}&month=${month}${accountParam}`,
    token,
  );
}
