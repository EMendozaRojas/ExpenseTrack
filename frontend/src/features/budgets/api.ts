import { apiFetch } from "../../api/client";
import type { Budget, BudgetInput, BudgetWithStatus } from "../transactions/types";

export function listBudgets(
  token: string,
  year: number,
  month: number,
): Promise<BudgetWithStatus[]> {
  return apiFetch<BudgetWithStatus[]>(`/budgets/?year=${year}&month=${month}`, token);
}

export function createBudget(token: string, payload: BudgetInput): Promise<Budget> {
  return apiFetch<Budget>("/budgets/", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateBudget(
  token: string,
  budgetId: number,
  payload: { amount?: string; is_active?: boolean },
): Promise<Budget> {
  return apiFetch<Budget>(`/budgets/${budgetId}`, token, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteBudget(token: string, budgetId: number): Promise<void> {
  return apiFetch<void>(`/budgets/${budgetId}`, token, { method: "DELETE" });
}
