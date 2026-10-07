<!-- Revisado 2026-10-07 antes de archivar: se implementó una versión más simple que la planificada (commit 63712d1, "carga de extractos CSV (US1)"). Las tareas reflejan lo implementado; el plan original completo figura en "Diferido". -->

## 1. Modelo y migración

- [x] 1.1 `app/models/import_batch.py` (owner_id, account_id, filename, status `previewed`/`committed`, range_start/range_end, strategy, contadores inserted/replaced/skipped, created_at, committed_at) y `app/models/import_row.py` (posted_at, amount, raw_description, external_hash, classification, matched_transaction_id, created_transaction_id); migración Alembic

## 2. Parseo y reconciliación

- [x] 2.1 `app/services/statement_parser.py`: CSV con reconocimiento de columnas por nombre (fecha, concepto, importe o debe/haber), formatos de fecha y decimal habituales; tests
- [x] 2.2 `app/services/reconciler.py`: `external_hash` (cuenta + fecha + importe + descripción normalizada) para `EXACT_DUPLICATE` y match difuso (mismo importe, ±1 día, similitud ≥85%) para `PROBABLE_DUPLICATE`; tests

## 3. API

- [x] 3.1 `POST /imports/` (multipart, cuenta propia, solo CSV, ≤5 MB y ≤10.000 filas) que devuelve la vista previa; `GET /imports/{id}`
- [x] 3.2 `POST /imports/{id}/commit` con estrategias `append_new`, `replace_range` y `replace_selected` + `row_ids`; categorización con reglas; 409 si ya estaba confirmada; tests

## 4. Frontend

- [x] 4.1 `features/imports/`: subida con selección de cuenta, vista previa con la clasificación de cada fila, elección de estrategia y resumen del resultado (hoy en un modal dentro de Movimientos); tests

## Diferido

Del plan original, no implementado:

- XLSX (`openpyxl`) y PDF; autodetección de separador y de encoding (`charset-normalizer`)
- Parseo en segundo plano (`BackgroundTasks`) con estados `pending`/`needs_mapping`/`needs_review`/`failed`
- Mapeo manual de columnas, firma de origen y tabla `import_mappings` con autoaplicación
- Estados `CONFLICT` y `MISSING_FROM_FILE`; resumen de solapamiento con movimientos existentes en el rango
- `external_hash` y `import_batch_id` en `transactions` con `UNIQUE(account_id, external_hash)`
- Traspaso de categoría/nota de los movimientos reemplazados en `replace_range`; recibos huérfanos (`receipts_not_carried_over`)
- `Idempotency-Key`, `POST /imports/{id}/undo`, `DELETE /imports/{id}` y `GET /imports`
- Verificación con `rapidfuzz` y fixtures de varios bancos; smoke end-to-end del plan original
