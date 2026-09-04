## Context

Ver `proposal.md` — Why. Depende de `accounts-and-transactions` (soft-delete, `source`, cuentas) y `hierarchical-categories-and-rules` (motor de reglas). Es el cambio con más riesgo técnico del roadmap (parseo heterogéneo, idempotencia, reconciliación). Este documento recoge las **decisiones abiertas** para la revisión.

## Goals / Non-Goals

**Goals:**
- Importar CSV/XLSX de forma robusta con mapeo reutilizable.
- Detectar duplicados y solapamiento de rango, y dejar que el usuario decida (añadir / reemplazar).
- No perder nunca los movimientos manuales ni el trabajo de categorización al reimportar.
- Commit atómico y reversible.

**Non-Goals:**
- Conexión a APIs bancarias / agregadores (PSD2). Solo archivo.
- OCR de extractos escaneados en el MVP.
- Parseo de PDF de todos los bancos: solo plantillas concretas y opt-in (ver D2).

## Decisions

> Estado de la revisión (2026-09-01): D1–D8 resueltas.

### D1 — Formatos en el MVP — DECIDIDO: CSV + XLSX
- Solo **CSV y XLSX**. PDF queda explícitamente fuera de este cambio (iteración futura: parser por plantilla de banco + pantalla de review como validación final).

### D2 — Detección de duplicados — DECIDIDO
- `external_hash = sha256(f"{account_id}|{posted_at_iso}|{amount_2dp}|{normalize_desc(raw_description)}")`. `normalize_desc` = mayúsculas, sin acentos, colapsar espacios, quitar `\d{4,}`. Fila del archivo con `external_hash` igual a un movimiento no borrado de la cuenta → `EXACT_DUPLICATE`.
- Match difuso → `PROBABLE_DUPLICATE`: misma cuenta, mismo `amount`, `posted_at` dentro de **±1 día**, y `rapidfuzz.token_set_ratio(desc_a, desc_b) >= 85`.
- `CONFLICT`: cumple el criterio difuso pero el archivo trae un campo que el movimiento existente no tiene (p. ej. `counterparty` vacío en BD y presente en el archivo).
- Los tres números (`±1`, `85`, longitud de `\d{4,}`) son constantes en `app/services/reconciler.py`, ajustables sin tocar el spec.

### D3 — Estrategias de commit y su semántica — DECIDIDO
- `append_new` (default): inserta solo filas `NEW`. No toca nada existente.
- `replace_range`: soft-delete de `transactions` de la cuenta en `[file_date_from, file_date_to]` con `source IN ('import','rule')`, marcadas `replaced_by_batch_id`; inserta todas las filas del archivo; el commit es una única transacción.
  - **Transferencias**: se crean siempre con `source='manual'` → **nunca** entran en el soft-delete de `replace_range`. Sin cascada entre cuentas, sin caso especial.
  - **Movimientos manuales / efectivo** (`source='manual'`): intactos.
  - **Traspaso de `category_id` / `note` / splits / adjuntos** de la fila reemplazada a la entrante:
    - match **exacto** (`external_hash`): traspaso automático.
    - match **difuso** (`PROBABLE_DUPLICATE`): traspaso **solo si el usuario marcó esa fila como duplicado** en el review.
  - **Recibo huérfano** (fila reemplazada con adjunto, sin fila entrante que lo herede): el adjunto se queda en el movimiento soft-deleted (recuperable con "deshacer"). El resultado del commit incluye `receipts_not_carried_over` (recuento) para que el frontend avise. El commit no se interrumpe.
- `replace_selected`: como `append_new` salvo las filas que el usuario marque "usar versión del archivo" (para `PROBABLE_DUPLICATE` / `CONFLICT`).

### D4 — Procesamiento en segundo plano — DECIDIDO: `BackgroundTasks`
- `BackgroundTasks` de FastAPI; el front hace polling de `GET /imports/{id}`. Suficiente para CSV/XLSX bajo el límite de filas en uvicorn single-process.
- Migración a ARQ/Celery + Redis solo si entran PDF o archivos grandes — fuera de alcance.

### D5 — Staging de filas parseadas — DECIDIDO: tabla `import_rows`
- Tabla `import_rows` (raw JSONB + campos normalizados + `classification` + `user_decision` + `matched_transaction_id`) ligada al batch. Permite el review fila a fila y re-commitear sin reparsear.

### D6 — Reutilización del mapeo de columnas — DECIDIDO: firma de origen automática
- Al parsear, el sistema deriva una **`source_signature`** de la estructura del propio archivo: hash de la lista normalizada de nombres de columna de la fila de cabecera + tokens de texto emisor de las primeras N filas (si los hay). No hay base de datos de bancos.
- El mapeo confirmado se guarda en una tabla `import_mappings (owner_id, source_signature, column_mapping JSONB, updated_at)`, `UNIQUE(owner_id, source_signature)`.
- En una subida posterior cuya `source_signature` coincida, el batch arranca ya en `needs_review` con el `column_mapping` aplicado (sin pasar por `needs_mapping`). El usuario puede corregirlo, lo que actualiza el mapeo guardado.
- Si la firma no casa nada y el mapeo es ambiguo → `needs_mapping` como hasta ahora.

### D7 — Límites — DECIDIDO
- Archivo **≤ 5 MB**, **≤ 10.000 filas** de datos por importación. Por encima: rechazo en `POST /imports` con mensaje que explica el límite, sin crear batch. Constantes en config.

### D8 — Idempotencia del commit — CONFIRMADO
- `POST /imports/{id}/commit` acepta header `Idempotency-Key`; un batch ya `committed` no se vuelve a commitear (409). Commit en una transacción de DB; si falla, el batch vuelve a `needs_review` sin cambios parciales.

## Risks / Trade-offs

- [PDF sin estándar, tablas multipágina, escaneados] → fuera del MVP; cuando entre, plantillas por banco + pantalla de review como validación final del usuario.
- [CSV/XLSX heterogéneos: separador, decimal `,`, fechas `DD/MM/YYYY`, latin-1, débito/crédito] → autodetección (`csv.Sniffer`, `charset-normalizer`, `dateutil`) + mapeo manual persistido; normalizador central a `Decimal`/`date` ISO; fixtures reales anonimizados de varios bancos en los tests.
- [Reimportar corrompe saldos] → `UNIQUE(account_id, external_hash)` + clasificación por fila + estrategia explícita; commit atómico; undo por soft-delete.
- [`replace_range` borra trabajo de categorización] → traspaso automático por match exacto y difuso-confirmado antes de borrar; los originales quedan soft-deleted (recuperables con "deshacer"); el commit reporta `receipts_not_carried_over` y el recuento de reemplazos para que el frontend avise.
- [Import bloquea el request] → parseo en `BackgroundTasks`, no en el handler de subida.
- [`source_signature` colisiona o no casa entre exports del mismo banco] → si no casa, se degrada a `needs_mapping` (comportamiento seguro, solo pierde el autocompletado); si colisiona entre dos formatos distintos, el usuario corrige el mapeo y se re-guarda. Nunca aplica un mapeo a ciegas sin que el usuario pueda verlo en el review.
- [Alertas de presupuesto no se disparan tras import masivo] → recalcular presupuestos al final del commit (idempotente); cron de reconciliación como respaldo (en `budgets-and-savings-goals`).

## Migration Plan

1. Migración de esquema: `import_batches`, `import_rows`, `import_mappings`; columnas `external_hash`, `import_batch_id`, `replaced_by_batch_id` en `transactions`; `UNIQUE(account_id, external_hash) WHERE external_hash IS NOT NULL`; `UNIQUE(owner_id, source_signature)` en `import_mappings`.
2. Sin data-migration (los movimientos existentes quedan con `external_hash NULL`; no participan en dedupe hasta que se toquen).
3. Dependencias nuevas en `requirements.txt`: `openpyxl`, `python-dateutil`, `charset-normalizer`, `rapidfuzz`. Verificar build de la imagen backend.
4. Rollback: `downgrade` elimina tablas y columnas nuevas.

## Open Questions

- ¿Se guarda el archivo original subido (para reparsear o auditar) o se descarta tras parsear? Propuesta: guardarlo en el mismo `StorageBackend` de adjuntos (cambio de multi-moneda/adjuntos) hasta que el batch se archive; no bloquea el MVP (se puede descartar tras parsear).
- ¿Formato de export propio de ExpenseTrack (round-trip) como formato "siempre soportado"? Se puede añadir después sin tocar el spec.
- Detección de recurrentes a partir de los movimientos importados: vive en `visual-dashboard-and-insights`, no aquí.
