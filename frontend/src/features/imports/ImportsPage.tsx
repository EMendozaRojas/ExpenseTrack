import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { useAuth } from "../auth/useAuth";
import { listAccounts } from "../transactions/api";
import { formatCurrency } from "../transactions/format";
import type { ImportCommitResult, ImportPreview, ImportStrategy } from "../transactions/types";
import { commitImport, uploadStatement } from "./api";

const CLASSIFICATION_LABELS: Record<string, string> = {
  NEW: "Nueva",
  EXACT_DUPLICATE: "Duplicado exacto",
  PROBABLE_DUPLICATE: "Posible duplicado",
};

interface ImportsPageProps {
  onCommitted?: () => void;
}

export function ImportsPage({ onCommitted }: ImportsPageProps = {}) {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [accountId, setAccountId] = useState<number | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [strategy, setStrategy] = useState<ImportStrategy>("append_new");
  const [selectedRowIds, setSelectedRowIds] = useState<Set<number>>(new Set());
  const [result, setResult] = useState<ImportCommitResult | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const accountsQuery = useQuery({
    queryKey: ["accounts"],
    queryFn: () => listAccounts(token as string),
    enabled: token !== null,
  });

  const uploadMutation = useMutation({
    mutationFn: () => uploadStatement(token as string, accountId as number, file as File),
    onSuccess: (data) => {
      setPreview(data);
      setResult(null);
      setUploadError(null);
      setSelectedRowIds(new Set());
      setStrategy("append_new");
    },
    onError: (error: Error) => setUploadError(error.message),
  });

  const commitMutation = useMutation({
    mutationFn: () =>
      commitImport(token as string, preview!.id, strategy, Array.from(selectedRowIds)),
    onSuccess: (data) => {
      setResult(data);
      void queryClient.invalidateQueries({ queryKey: ["transactions"] });
      void queryClient.invalidateQueries({ queryKey: ["summary"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      void queryClient.invalidateQueries({ queryKey: ["preferences"] });
      void queryClient.invalidateQueries({ queryKey: ["accounts"] });
      onCommitted?.();
    },
  });

  const hasDuplicates = useMemo(
    () => (preview ? preview.exact_duplicate_count + preview.probable_duplicate_count > 0 : false),
    [preview],
  );

  function toggleRow(rowId: number) {
    setSelectedRowIds((previous) => {
      const next = new Set(previous);
      if (next.has(rowId)) {
        next.delete(rowId);
      } else {
        next.add(rowId);
      }
      return next;
    });
  }

  const accounts = accountsQuery.data ?? [];

  return (
    <div className="imports-page">
      <p className="page-status">
        Por ahora solo CSV (máx. 5 MB / 10.000 filas). XLSX y PDF llegarán en un próximo cambio.
      </p>

      <div className="import-upload-form">
        <label htmlFor="import-account">Cuenta</label>
        <select
          id="import-account"
          value={accountId ?? ""}
          onChange={(event) => setAccountId(event.target.value ? Number(event.target.value) : null)}
        >
          <option value="">Selecciona una cuenta</option>
          {accounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name}
            </option>
          ))}
        </select>

        <label htmlFor="import-file">Archivo CSV</label>
        <input
          id="import-file"
          type="file"
          accept=".csv"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />

        <button
          type="button"
          disabled={!accountId || !file || uploadMutation.isPending}
          onClick={() => uploadMutation.mutate()}
        >
          {uploadMutation.isPending ? "Analizando..." : "Previsualizar"}
        </button>

        {uploadError && <p className="form-error">{uploadError}</p>}
      </div>

      {preview && (
        <section className="import-preview">
          <h2>Previsualización: {preview.filename}</h2>
          <p className="page-status">
            {preview.range_start} a {preview.range_end} · {preview.new_count} nuevas ·{" "}
            {preview.exact_duplicate_count} duplicados exactos · {preview.probable_duplicate_count}{" "}
            posibles duplicados
          </p>

          <table className="import-rows-table">
            <thead>
              <tr>
                <th></th>
                <th>Fecha</th>
                <th>Descripción</th>
                <th>Importe</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {preview.rows.map((row) => (
                <tr key={row.id} className={`import-row-${row.classification}`}>
                  <td>
                    {row.classification !== "NEW" && (
                      <input
                        type="checkbox"
                        checked={selectedRowIds.has(row.id)}
                        onChange={() => toggleRow(row.id)}
                        aria-label={`Incluir fila ${row.raw_description}`}
                      />
                    )}
                  </td>
                  <td>{row.posted_at}</td>
                  <td>{row.raw_description}</td>
                  <td>{formatCurrency(Number(row.amount))}</td>
                  <td>{CLASSIFICATION_LABELS[row.classification]}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="import-strategy">
            <label htmlFor="import-strategy-select">Estrategia de confirmación</label>
            <select
              id="import-strategy-select"
              value={strategy}
              onChange={(event) => setStrategy(event.target.value as ImportStrategy)}
            >
              <option value="append_new">Añadir solo las nuevas</option>
              {hasDuplicates && (
                <>
                  <option value="replace_range">
                    Reemplazar el rango ({preview.range_start} a {preview.range_end})
                  </option>
                  <option value="replace_selected">Reemplazar solo las filas marcadas</option>
                </>
              )}
            </select>
            {hasDuplicates && strategy !== "append_new" && (
              <p className="page-status">
                {strategy === "replace_range"
                  ? "Se sustituirán todos los movimientos importados/por regla en ese rango; lo editado a mano no se toca."
                  : "Marca arriba las filas duplicadas que quieres reemplazar."}
              </p>
            )}
          </div>

          <button
            type="button"
            disabled={commitMutation.isPending}
            onClick={() => commitMutation.mutate()}
          >
            {commitMutation.isPending ? "Confirmando..." : "Confirmar importación"}
          </button>

          {result && (
            <p className="import-result">
              Hecho: {result.inserted_count} insertados, {result.replaced_count} reemplazados,{" "}
              {result.skipped_count} omitidos.
            </p>
          )}
        </section>
      )}
    </div>
  );
}
