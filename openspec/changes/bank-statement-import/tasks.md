<!-- Decisiones D1–D8 resueltas en design.md (revisión 2026-09-01). CSV+XLSX, BackgroundTasks, firma de origen automática, ±1d/ratio 85, ≤5MB/≤10k filas. Listo para /opsx:apply. -->

## 1. Modelo y migración

- [ ] 1.1 `app/models/import_batch.py` (account_id, owner_id, original_filename, format, status, source_signature, column_mapping JSONB, file_date_from/to, strategy, contadores inc. `receipts_not_carried_over`, created_at, committed_at)
- [ ] 1.2 `app/models/import_row.py` staging (batch_id, raw JSONB, parsed: posted_at/amount/description, classification, user_decision, matched_transaction_id)
- [ ] 1.3 `app/models/import_mapping.py` (owner_id, source_signature, column_mapping JSONB, updated_at) + `UNIQUE(owner_id, source_signature)`
- [ ] 1.4 Columnas en `transactions`: `external_hash`, `import_batch_id`, `replaced_by_batch_id`; `UNIQUE(account_id, external_hash) WHERE external_hash IS NOT NULL`; migración Alembic (sin data-migration)
- [ ] 1.5 Añadir `openpyxl`, `python-dateutil`, `charset-normalizer`, `rapidfuzz` a `requirements.txt`; verificar build de la imagen backend

## 2. Parsers y normalización

- [ ] 2.1 `app/services/parsers/csv_parser.py`: autodetección separador (`csv.Sniffer`), encoding (`charset-normalizer`), decimal, fecha (`dateutil`); tests con fixtures anonimizados de ≥3 bancos
- [ ] 2.2 `app/services/parsers/xlsx_parser.py` con `openpyxl`; test con fixture XLSX
- [ ] 2.3 Normalizador central → `Decimal` firmado + `date` ISO; columnas débito/crédito separadas → un importe firmado; tests de casos límite (decimal `,`, `DD/MM/YYYY`, importe entre paréntesis, latin-1)
- [ ] 2.4 `source_signature`: hash de nombres de columna de cabecera normalizados + tokens emisor de las primeras N filas; test de estabilidad entre dos exports del mismo formato y de diferencia entre formatos distintos
- [ ] 2.5 `external_hash = sha256(account_id|posted_at_iso|amount_2dp|normalize_desc)`; `normalize_desc` (mayúsc., sin acentos, sin `\d{4,}`, colapsar espacios); tests

## 3. Reconciliación

- [ ] 3.1 `app/services/reconciler.py`: clasificación por fila —`EXACT_DUPLICATE` (hash), `PROBABLE_DUPLICATE` (misma cuenta+importe, fecha ±1d, `rapidfuzz.token_set_ratio >= 85`), `CONFLICT` (difuso + campo nuevo en archivo), `MISSING_FROM_FILE`, `NEW`— y resumen de solapamiento (rango, existentes en rango import vs manual); tests por cada estado; constantes ±1/85 en config
- [ ] 3.2 Commit `append_new`: inserta solo `NEW`; test de contadores 12/0/38
- [ ] 3.3 Commit `replace_range` en una transacción: soft-delete `source IN ('import','rule')` en rango (marca `replaced_by_batch_id`), respeta `manual` y patas de transferencia, inserta filas del archivo; traspaso de `category_id`/splits/`note` automático en match exacto y en difuso solo si `user_decision=duplicate`; recibos huérfanos se quedan en el soft-deleted y suman a `receipts_not_carried_over`; tests: preserva manuales+transferencia, traspaso exacto sí / difuso no confirmado no, contador de recibos huérfanos
- [ ] 3.4 Commit `replace_selected`: como `append_new` salvo filas marcadas "usar archivo"; test
- [ ] 3.5 `POST /imports/{id}/undo` sobre batch `committed`: quita los insertados, restaura los reemplazados; test de restauración al estado previo
- [ ] 3.6 Tras commit: aplicar reglas de categorización a los movimientos nuevos; recalcular presupuestos si `budgets-and-savings-goals` ya está aplicado (hook opcional)

## 4. API y background

- [ ] 4.1 `app/routers/imports.py`: `POST /imports` (multipart, valida cuenta propia y límites ≤5MB/≤10k filas → 404/413), `GET /imports/{id}` (estado + review), `PATCH /imports/{id}/mapping` (re-parsea y guarda en `import_mappings`), `POST /imports/{id}/commit` (`strategy` + `Idempotency-Key`, 409 si ya `committed`), `POST /imports/{id}/undo`, `DELETE /imports/{id}`, `GET /imports`
- [ ] 4.2 Parseo en `BackgroundTasks`: `pending`→(`source_signature` casa mapeo → `needs_review` con mapping aplicado | ambiguo → `needs_mapping` | ok → `needs_review`); test de los tres caminos
- [ ] 4.3 Test de que un `source_signature` conocido salta `needs_mapping`

## 5. Frontend

- [ ] 5.1 `features/imports/`: subida con selección de cuenta; polling de estado
- [ ] 5.2 Pantalla de mapeo de columnas (aparece solo si `needs_mapping`; prefill si la firma casaba)
- [ ] 5.3 Tabla de review: estado por fila, marcar `PROBABLE_DUPLICATE`/`CONFLICT` como duplicado/usar-archivo, resumen de solapamiento, selector de estrategia con copy explicativo; resumen post-commit (incl. aviso de `receipts_not_carried_over`); acción "deshacer"
- [ ] 5.4 Tests de `features/imports`

## 6. Verificación

- [ ] 6.1 Backend `ruff`/`mypy`/`pytest --cov` (≥70%); Frontend `eslint`/`tsc`/`vitest --coverage` (≥70%)
- [ ] 6.2 Smoke end-to-end: importar un CSV, revisar, `append_new`; reimportar el mismo mes ampliado con `replace_range` y verificar que los movimientos en efectivo, la transferencia y las categorías manuales sobreviven, y que las categorías de los duplicados exactos se traspasan; deshacer y comprobar restauración; volver a subir el mismo formato y ver que el mapeo se autoaplica
