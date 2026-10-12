import { apiFetch } from "../../api/client";
import type {
  GoalContribution,
  GoalInput,
  GoalProjection,
  SavingsGoal,
} from "../transactions/types";

export function listGoals(token: string): Promise<SavingsGoal[]> {
  return apiFetch<SavingsGoal[]>("/goals/", token);
}

export function createGoal(token: string, payload: GoalInput): Promise<SavingsGoal> {
  return apiFetch<SavingsGoal>("/goals/", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateGoal(
  token: string,
  goalId: number,
  payload: Partial<GoalInput> & { status?: string },
): Promise<SavingsGoal> {
  return apiFetch<SavingsGoal>(`/goals/${goalId}`, token, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteGoal(token: string, goalId: number): Promise<void> {
  return apiFetch<void>(`/goals/${goalId}`, token, { method: "DELETE" });
}

export function addContribution(
  token: string,
  goalId: number,
  payload: { amount: string; contributed_at: string; note?: string | null },
): Promise<GoalContribution> {
  return apiFetch<GoalContribution>(`/goals/${goalId}/contributions`, token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listContributions(token: string, goalId: number): Promise<GoalContribution[]> {
  return apiFetch<GoalContribution[]>(`/goals/${goalId}/contributions`, token);
}

export function deleteContribution(
  token: string,
  goalId: number,
  contributionId: number,
): Promise<void> {
  return apiFetch<void>(`/goals/${goalId}/contributions/${contributionId}`, token, {
    method: "DELETE",
  });
}

export function getProjection(token: string, goalId: number): Promise<GoalProjection> {
  return apiFetch<GoalProjection>(`/goals/${goalId}/projection`, token);
}
