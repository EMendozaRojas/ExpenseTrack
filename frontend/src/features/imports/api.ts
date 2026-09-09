import { API_BASE_URL, ApiError, apiFetch } from "../../api/client";
import type { ImportCommitResult, ImportPreview, ImportStrategy } from "../transactions/types";

export async function uploadStatement(
  token: string,
  accountId: number,
  file: File,
): Promise<ImportPreview> {
  const formData = new FormData();
  formData.append("account_id", String(accountId));
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/imports/`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail =
      typeof body?.detail === "string" ? body.detail : `La petición falló con estado ${response.status}`;
    throw new ApiError(response.status, detail);
  }

  return response.json() as Promise<ImportPreview>;
}

export function commitImport(
  token: string,
  batchId: number,
  strategy: ImportStrategy,
  rowIds: number[],
): Promise<ImportCommitResult> {
  return apiFetch<ImportCommitResult>(`/imports/${batchId}/commit`, token, {
    method: "POST",
    body: JSON.stringify({ strategy, row_ids: rowIds }),
  });
}
