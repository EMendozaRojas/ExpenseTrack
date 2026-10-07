<!-- Revisado 2026-10-07 antes de archivar: specs ajustadas al comportamiento actual (incluye la cuenta principal y la papelera de 30 días, añadidas después sin change propio). Lo no implementado figura en "Diferido". -->

## 1. Modelo y migración (backend)

- [x] 1.1 Crear `app/models/account.py` (`Account`: id, owner_id, name, type, currency, initial_balance `Numeric(14,2)`, is_archived, created_at, updated_at) y verificar con un test de modelo que se crea y relaciona con `User`
- [x] 1.2 Reescribir `app/models/expense.py` → `app/models/transaction.py` (`Transaction`: amount `Numeric(14,2)` firmado, direction, account_id, owner_id, posted_at, category_id nullable, counterparty, raw_description, note, source, transfer_group_id, created_at, updated_at, deleted_at); actualizar `models/__init__.py`
- [x] 1.3 Generar migración Alembic: tabla `accounts`; transformar `expenses`→`transactions` con nuevas columnas y `amount` negativo para los gastos migrados; índices `(owner_id, posted_at DESC) WHERE deleted_at IS NULL`, `(account_id, posted_at)`, `transfer_group_id`
- [x] 1.4 Data-migration en la misma revisión: crear cuenta `name='Efectivo'`, `type='cash'`, `currency='EUR'` por `owner_id` y asignar `account_id`; poner `amount` en negativo y `direction='expense'`, `source='manual'`; verificar con `alembic upgrade head` + `downgrade` en base de prueba
- [x] 1.5 Cambiar `create_access_token` a `sub=str(user.id)` y `get_current_user` a búsqueda por id; ajustar tests de auth; nota en el PR de que caducan las sesiones abiertas

## 2. Schemas y API (backend)

- [x] 2.1 `app/schemas/account.py` (Create/Read con `balance` calculado) y `app/schemas/transaction.py` (Create/Update/Read, validación de signo↔`direction` y `amount != 0`, envelope `{items, next_cursor}`); tests de validación por cada `direction`
- [x] 2.2 `app/routers/accounts.py`: `GET/POST/PATCH /accounts`, `POST /accounts/{id}/archive`, `GET /accounts/{id}/balance` (saldo actual, `SUM()` en SQL con `deleted_at IS NULL`); tests de aislamiento (404 en cuenta ajena) y de archivado con movimientos
- [x] 2.3 `app/routers/transactions.py`: `GET` con filtros (account, category, direction, date_from/to, q) + paginación keyset `(posted_at DESC, id DESC)`, default 50 / máx 200; `POST`, `PATCH` (mismas reglas de validación que `POST`), `DELETE` (soft); reusar checks de pertenencia y de visibilidad de categoría; tests incl. editar/borrar movimiento ajeno → 404
- [x] 2.4 `POST /transactions/transfer`: crea las dos patas con `transfer_group_id`; `DELETE` sobre una pata hace soft-delete de todo el grupo; tests: ambas cuentas deben ser del usuario, y borrar una pata borra las dos y cuadra saldos
- [x] 2.5 Reescribir `GET /expenses/summary` sobre `transactions` con filtro por rango `[inicio_mes, inicio_mes_siguiente)` (sin `extract()`), `SUM()` en SQL; mantener el shape de respuesta; actualizar sus tests
- [x] 2.6 Registrar routers en `main.py`
- [x] 2.7 Archivar el change `edit-expense` como supersedido por `accounts-and-transactions` (no se implementa su `PUT`)

## 3. Frontend

- [x] 3.1 Renombrar `features/expenses/` → `features/transactions/`; actualizar imports y rutas; test de humo verde
- [x] 3.2 API + tipos + hooks de cuentas con `@tanstack/react-query` (consolidado en `features/transactions/api.ts` en vez de una carpeta `features/accounts/` separada — mismo resultado, menos indirección)
- [x] 3.3 Selector de cuenta en `TransactionsPage`; el alta de movimiento incluye `account_id` y `direction`
- [x] 3.4a `TransactionForm`/`TransactionList` adaptados a importe firmado e ingreso/gasto (`Math.abs()` + color); tests
## 4. Verificación

- [x] 4.1 Backend: `ruff`, `mypy`, `pytest --cov` (≥70%); Frontend: `eslint`, `tsc`, `vitest --coverage` (≥70%)
- [x] 4.2 Smoke end-to-end contra el stack: crear cuenta, registrar ingreso y gasto, hacer transferencia, borrar una pata y comprobar que desaparecen ambas y los saldos cuadran, revisar `summary`
- [x] 4.3 Verificar `alembic downgrade` deja el esquema en el estado previo en una copia de la base

## Diferido

- 3.4b UI para crear transferencias (`POST /transactions/transfer` no tiene formulario) y confirmación al borrar una — hoy las filas de transferencia no muestran botón "Eliminar" en la lista, así que el caso no es alcanzable desde la UI. El backend lo soporta y está testeado (`test_create_transfer`, `test_deleting_one_leg_deletes_both`).
