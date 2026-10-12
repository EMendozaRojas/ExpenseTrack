import { API_BASE_URL, apiFetch, authorizedFetch, throwIfNotOk } from "../../api/client";
import type { ImportCommitResult, ImportPreview, ImportStrategy } from "../transactions/types";

export async function uploadStatement(
  token: string,
  accountId: number,
  file: File,
): Promise<ImportPreview> {
  const formData = new FormData();
  formData.append("account_id", String(accountId));
  formData.append("file", file);

  const response = await authorizedFetch(`${API_BASE_URL}/imports/`, token, {
    method: "POST",
    body: formData,
  });

  await throwIfNotOk(response);

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
