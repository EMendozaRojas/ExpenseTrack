import { apiFetch } from "../../api/client";
import type {
  BudgetCopyPreviewItem,
  BudgetCopyResult,
  BudgetInput,
  BudgetRecommendation,
  BudgetScope,
  BudgetUpdateInput,
  BudgetWithStatus,
  PlannedBudgetMonth,
} from "../transactions/types";

export function listBudgets(
  token: string,
  year: number,
  month: number,
): Promise<BudgetWithStatus[]> {
  return apiFetch<BudgetWithStatus[]>(`/budgets/?year=${year}&month=${month}`, token);
}

export function createBudget(token: string, payload: BudgetInput): Promise<BudgetWithStatus> {
  return apiFetch<BudgetWithStatus>("/budgets/", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateBudget(
  token: string,
  categoryId: number,
  period: string,
  payload: BudgetUpdateInput,
): Promise<BudgetWithStatus> {
  return apiFetch<BudgetWithStatus>(`/budgets/${categoryId}/${period}`, token, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteBudget(
  token: string,
  categoryId: number,
  period: string,
  scope: BudgetScope,
): Promise<void> {
  return apiFetch<void>(`/budgets/${categoryId}/${period}?scope=${scope}`, token, {
    method: "DELETE",
  });
}

export function listPlannedMonths(
  token: string,
  categoryId: number,
  from: string,
): Promise<PlannedBudgetMonth[]> {
  return apiFetch<PlannedBudgetMonth[]>(`/budgets/${categoryId}/planned?from=${from}`, token);
}

export function getCopyPreview(
  token: string,
  year: number,
  month: number,
): Promise<BudgetCopyPreviewItem[]> {
  return apiFetch<BudgetCopyPreviewItem[]>(
    `/budgets/copy-preview?year=${year}&month=${month}`,
    token,
  );
}

export function copyBudgets(
  token: string,
  payload: { year: number; month: number; items: { category_id: number; amount: string }[] },
): Promise<BudgetCopyResult> {
  return apiFetch<BudgetCopyResult>("/budgets/copy", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listRecommendations(
  token: string,
  categoryId?: number,
): Promise<BudgetRecommendation[]> {
  const query = categoryId === undefined ? "" : `?category_id=${categoryId}`;
  return apiFetch<BudgetRecommendation[]>(`/budgets/recommendations${query}`, token);
}
