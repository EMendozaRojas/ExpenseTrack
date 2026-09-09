import { API_BASE_URL, ApiError, apiFetch } from "../../api/client";
import type { Attachment } from "./types";

export function listAttachments(token: string, transactionId: number): Promise<Attachment[]> {
  return apiFetch<Attachment[]>(`/transactions/${transactionId}/attachments`, token);
}

export async function uploadAttachment(
  token: string,
  transactionId: number,
  file: File,
): Promise<Attachment> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/transactions/${transactionId}/attachments`, {
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

  return response.json() as Promise<Attachment>;
}

export function deleteAttachment(token: string, attachmentId: number): Promise<void> {
  return apiFetch<void>(`/attachments/${attachmentId}`, token, { method: "DELETE" });
}

export async function fetchAttachmentBlob(token: string, attachmentId: number): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/attachments/${attachmentId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new ApiError(response.status, "No se pudo abrir el adjunto");
  }
  return response.blob();
}
