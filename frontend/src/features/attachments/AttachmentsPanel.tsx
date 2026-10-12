import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { useAuth } from "../auth/useAuth";
import { deleteAttachment, fetchAttachmentBlob, listAttachments, uploadAttachment } from "./api";

interface AttachmentsPanelProps {
  transactionId: number;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(0)} KB`;
}

export function AttachmentsPanel({ transactionId }: AttachmentsPanelProps) {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const attachmentsQuery = useQuery({
    queryKey: ["attachments", transactionId],
    queryFn: () => listAttachments(token as string, transactionId),
    enabled: token !== null,
  });

  const uploadMutation = useMutation({
    mutationFn: () => uploadAttachment(token as string, transactionId, file as File),
    onSuccess: () => {
      setFile(null);
      setUploadError(null);
      void queryClient.invalidateQueries({ queryKey: ["attachments", transactionId] });
    },
    onError: (error: Error) => setUploadError(error.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (attachmentId: number) => deleteAttachment(token as string, attachmentId),
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: ["attachments", transactionId] }),
  });

  async function handleView(attachmentId: number) {
    const blob = await fetchAttachmentBlob(token as string, attachmentId);
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  }

  const attachments = attachmentsQuery.data ?? [];

  return (
    <div className="attachments-panel">
      {attachmentsQuery.isLoading && <p className="page-status">Cargando adjuntos...</p>}
      {!attachmentsQuery.isLoading && attachments.length === 0 && (
        <p className="page-status">Sin recibos adjuntos.</p>
      )}
      <ul className="attachments-list">
        {attachments.map((attachment) => (
          <li key={attachment.id} className="attachments-list-item">
            <button
              type="button"
              className="attachments-link"
              onClick={() => void handleView(attachment.id)}
            >
              {attachment.filename}
            </button>
            <span className="page-status">{formatSize(attachment.size_bytes)}</span>
            <button
              type="button"
              className="button-secondary"
              onClick={() => deleteMutation.mutate(attachment.id)}
              disabled={deleteMutation.isPending}
            >
              Borrar
            </button>
          </li>
        ))}
      </ul>

      <div className="attachments-upload">
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp,application/pdf"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        <button
          type="button"
          disabled={!file || uploadMutation.isPending}
          onClick={() => uploadMutation.mutate()}
        >
          Subir recibo
        </button>
      </div>
      {uploadError && <p className="form-error">{uploadError}</p>}
    </div>
  );
}
