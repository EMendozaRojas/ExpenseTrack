import { apiFetch } from "../../api/client";
import type { AntSpendingGroup, InsightSettings, RecurringSeries } from "../transactions/types";

export function listRecurringSeries(token: string): Promise<RecurringSeries[]> {
  return apiFetch<RecurringSeries[]>("/insights/recurring", token);
}

export function dismissRecurringSeries(token: string, seriesKey: string): Promise<void> {
  return apiFetch<void>("/insights/recurring/dismiss", token, {
    method: "POST",
    body: JSON.stringify({ series_key: seriesKey }),
  });
}

export function restoreRecurringSeries(token: string, seriesKey: string): Promise<void> {
  return apiFetch<void>("/insights/recurring/restore", token, {
    method: "POST",
    body: JSON.stringify({ series_key: seriesKey }),
  });
}

export function listAntSpending(
  token: string,
  year: number,
  month: number,
): Promise<AntSpendingGroup[]> {
  return apiFetch<AntSpendingGroup[]>(`/insights/ant-spending?year=${year}&month=${month}`, token);
}

export function getInsightSettings(token: string): Promise<InsightSettings> {
  return apiFetch<InsightSettings>("/insights/settings", token);
}

export function updateInsightSettings(
  token: string,
  payload: Partial<InsightSettings>,
): Promise<InsightSettings> {
  return apiFetch<InsightSettings>("/insights/settings", token, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
