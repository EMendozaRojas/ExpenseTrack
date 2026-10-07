<!-- Revisado 2026-10-07 antes de archivar: se implementó una versión más simple (solo CSV, parseo síncrono, sin mapeo manual ni deshacer). La spec describe lo implementado; lo demás figura como "Diferido" en tasks.md. -->

## Why

Introducir los movimientos a mano no escala. El usuario quiere subir el extracto del banco (CSV/XLSX y, más adelante, PDF) y que el sistema cree los movimientos, los categorice con las reglas existentes y detecte duplicados. El caso crítico: un extracto previo pudo llegar **incompleto** y el usuario necesita poder **reemplazarlo**, no solo "saltar duplicados".

## What Changes

- Nuevo recurso `imports`: subida de archivo (`multipart`) asociada a una cuenta, parseo **en segundo plano** (`BackgroundTasks`), y estado (`pending` → `parsed`/`needs_mapping` → `needs_review` → `committed`/`failed`). Límites: ≤ 5 MB y ≤ 10.000 filas.
- Parsers: **CSV y XLSX** en el MVP (autodetección de separador, decimal, fecha, encoding; columnas débito/crédito separadas o importe firmado). PDF queda fuera de este cambio.
- Mapeo de columnas: el sistema deriva una **firma de origen** de la estructura del archivo (nombres de columnas de cabecera + texto emisor); el mapeo confirmado se guarda por `(owner_id, source_signature)` en `import_mappings` y se autoaplica en subidas futuras con la misma firma.
- Reconciliación de solapamiento: la respuesta de review clasifica cada fila (`NEW`, `EXACT_DUPLICATE`, `PROBABLE_DUPLICATE`, `CONFLICT`, `MISSING_FROM_FILE`) y reporta el rango de fechas del archivo y cuántos movimientos ya existen en ese rango.
- Estrategias de commit elegibles por el usuario: `append_new` (por defecto), `replace_range` (soft-delete de los movimientos `import`/`rule` del rango — respeta `manual` y las patas de transferencia — con traspaso de categoría/splits/nota: automático en match exacto, y en match difuso solo si el usuario lo confirmó), `replace_selected`.
- Dedupe por `external_hash` = `sha256(account_id | posted_at ISO | amount 2dp | descripción normalizada)` con `UNIQUE(account_id, external_hash)` como red de seguridad a nivel de fila. Difuso: misma cuenta+importe, fecha ±1 día, `token_set_ratio >= 85`.
- Commit en una sola transacción; `Idempotency-Key`; contadores (`inserted`/`replaced`/`skipped`/`receipts_not_carried_over`) y estrategia guardados en el batch; undo vía soft-delete.
- Tras el commit se aplican las reglas de categorización a los movimientos nuevos.

## Capabilities

### New Capabilities
- `statement-import`: carga de extractos bancarios en archivo, parseo y mapeo de columnas, previsualización con clasificación de duplicados y solapamiento, y confirmación con estrategia de reconciliación (añadir nuevos / reemplazar rango / reemplazar seleccionados) que preserva los movimientos manuales y el trabajo de categorización.

### Modified Capabilities

(ninguna archivada; la interacción con `transactions` — soft-delete, `source='import'`, `external_hash` — se especifica aquí.)

## Impact

- **Backend**: `app/models/import_batch.py`, `app/models/import_row.py` (staging), `app/models/import_mapping.py` (`owner_id`, `source_signature`, `column_mapping`); columnas `external_hash`, `import_batch_id`, `replaced_by_batch_id` en `transactions`; `app/routers/imports.py`; `app/services/parsers/` (csv, xlsx), `app/services/reconciler.py`; tareas en segundo plano (FastAPI `BackgroundTasks`); dependencias nuevas: `openpyxl`, `python-dateutil`, `charset-normalizer`, `rapidfuzz`.
- **Frontend**: `features/imports/` — subida, pantalla de mapeo, tabla de review con estados por fila y selector de estrategia, resumen post-commit.
- **Orden**: depende de `accounts-and-transactions` y de `hierarchical-categories-and-rules` (para aplicar reglas tras el commit).
