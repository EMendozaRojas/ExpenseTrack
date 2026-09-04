## Context

Ver `proposal.md` — Why. Estado actual: modelo `User` / `Category` / `Expense`, JWT con `sub = email`, queries filtradas por `owner_id`, `Expense.amount` positivo `Numeric(10,2)`, sin paginación, `summary` suma en Python. Este documento recoge las **decisiones abiertas** a resolver en la revisión antes de escribir specs/tasks definitivos.

## Goals / Non-Goals

**Goals:**
- Modelo de datos que soporte ingresos, gastos y transferencias sobre cuentas.
- Saldo por cuenta y saldo total consultables.
- Migración sin pérdida de los gastos ya registrados.
- Aislamiento por usuario mantenido (y reforzable con RLS más adelante).

**Non-Goals:**
- Importación de extractos (cambio `bank-statement-import`).
- Multi-moneda real / conversión (cambio `multicurrency-social-auth-attachments`).
- Categorías jerárquicas y reglas (cambio `hierarchical-categories-and-rules`).
- Presupuestos, metas, dashboard visual.

## Decisions

> Estado de la revisión (2026-09-01): D1–D6 resueltas. D7 y D8 confirmadas.

### D1 — Signo del importe — DECIDIDO: firmado + `direction` explícito
- `amount` firmado: negativo = salida, positivo = entrada. **Y además** `direction` (`income` | `expense` | `transfer`) como columna propia.
- Motivo: `SUM(amount)` directo para el saldo; filtros por tipo triviales; patrón estándar (YNAB, Actual Budget, GnuCash). El signo "negativo" solo se ve en BD; el frontend muestra `Math.abs()` + color.
- Invariante: para `income`/`expense`, `direction` SHALL ser coherente con el signo (expense → amount < 0, income → amount > 0). `amount` no puede ser 0.
- Alternativa descartada: `amount` siempre positivo + `CASE WHEN direction=...` en cada agregación.

### D2 — JWT `sub` — DECIDIDO: pasar a `user.id` en este cambio
- `create_access_token` usa `sub = str(user.id)`; `get_current_user` resuelve por id.
- Motivo: cambio mínimo que desbloquea la reforma de auth (social + refresh) sin una migración de tokens posterior. Sin usuarios en producción.
- Coste asumido: invalida las sesiones abiertas al desplegar. Documentar en el PR.

### D3 — Cuenta por defecto en la migración — DECIDIDO: "Efectivo" / `type='cash'`
- Cada usuario con gastos recibe una cuenta `name='Efectivo'`, `type='cash'`, `currency='EUR'`, `initial_balance=0`; todos sus movimientos migrados se cuelgan de ella. El usuario puede renombrarla después.
- Alternativa descartada: `account_id` nullable hasta que el usuario cree una cuenta (complica las queries de saldo).

### D4 — Saldo `as_of` — DECIDIDO: posponer
- El MVP expone solo el **saldo actual** (`initial_balance + SUM(amount) WHERE deleted_at IS NULL`) en `GET /accounts` y `GET /accounts/{id}/balance` (sin parámetro de fecha).
- El saldo a fecha arbitraria (`as_of`) lo necesita la línea de tendencia → lo añadirá el cambio `visual-dashboard-and-insights`. No cambia el spec de creación de movimientos.
- Cacheo del saldo (columna/vista materializada): solo si se mide lentitud; fuera de alcance.

### D5 — Borrado de una transferencia — DECIDIDO: borrar ambas patas
- Una transferencia son dos filas con el mismo `transfer_group_id uuid`, `direction='transfer'`, `category_id NULL`.
- `DELETE` sobre cualquiera de las dos hace **soft-delete de todo el `transfer_group_id`** (ambas patas). El frontend confirma antes ("es una transferencia, se borran los dos apuntes").
- Editar el importe de una pata de transferencia queda fuera de alcance del MVP (se borra y se recrea); revisitar si molesta.
- Las transferencias se excluyen de los totales de ingreso/gasto en stats.

### D6 — `edit-expense` — DECIDIDO: plegarlo aquí y archivarlo como supersedido
- `PATCH /transactions/{id}` de este cambio cubre lo que pedía `edit-expense` (editar `amount`, `posted_at`, `category_id`, `direction`, `counterparty`, `note` con check de pertenencia y de visibilidad de categoría).
- Acción: no se implementa `edit-expense` por separado; al aplicar este cambio se archiva `edit-expense` con nota "supersedido por `accounts-and-transactions`". Sus escenarios se reflejan en el spec de `transactions`.

### D7 — Precisión y tipo — CONFIRMADO
- `Numeric(14,2)` (sube de 10,2 para dar margen a saldos anuales agregados). Dinero como **string** en JSON. `SUM()` en SQL, nunca en Python.
- `currency CHAR(3)` en `accounts` y `transactions` desde ya (default `'EUR'`), aunque la conversión no exista todavía.

### D8 — Paginación — CONFIRMADO
- `GET /transactions` con `limit` (default **50**, máx 200) + `cursor` (keyset sobre `(posted_at DESC, id DESC)`), no offset. La respuesta es un envelope `{ items, next_cursor }`.

## Risks / Trade-offs

- [Migración destructiva de `expenses`] → hacer `pg_dump` previo; migración Alembic en una transacción; probar `upgrade` + `downgrade` en copia local antes de aplicar.
- [Romper el frontend actual de golpe] → renombrar `features/expenses` → `features/transactions` en el mismo PR y mantener el test de humo verde; no hay usuarios en producción.
- [`extract()` sigue en `summary`] → este cambio ya reescribe esa query a filtro por rango `[inicio_mes, inicio_mes_siguiente)` con índice `(owner_id, posted_at)`.
- [Cambiar `sub` del JWT rompe sesiones abiertas] → aceptable; documentar en el PR.
- [Coherencia signo ↔ `direction`] → validar en el schema Pydantic de entrada (no confiar solo en el frontend); test unitario por cada `direction`.
- [Borrar una pata de transferencia deja saldos descuadrados] → el `DELETE` cascada al `transfer_group_id` lo cubre en backend; el frontend solo añade la confirmación.

## Migration Plan

1. `pg_dump` de la base local.
2. Migración Alembic: crear `accounts`; renombrar/ampliar `expenses` → `transactions` (nuevas columnas, `amount` a `Numeric(14,2)`, signo negativo para los gastos migrados, `direction='expense'`, `source='manual'`, `deleted_at NULL`).
3. Data-migration: por cada `owner_id` distinto en `transactions`, crear cuenta `name='Efectivo'`, `type='cash'`, `currency='EUR'` y set `account_id`.
4. Índices: `(owner_id, posted_at DESC) WHERE deleted_at IS NULL`, `(account_id, posted_at)`, `transfer_group_id`.
5. JWT: desplegar el cambio de `sub` a `user.id` con el mismo PR; las sesiones abiertas caducan (aceptado).
6. Archivar el change `edit-expense` como supersedido (`openspec archive edit-expense` o nota manual) una vez este cambio esté aplicado.
7. Rollback: `downgrade` revierte esquema; los datos se restauran del dump si hace falta.

## Open Questions

- ¿Se numeran las cuentas con un orden manual (`sort_order`) para el frontend? Se puede añadir después sin romper nada — no bloquea.
