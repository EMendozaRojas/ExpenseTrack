## Why

Hoy el modelo solo registra **salidas** (`Expense`) sueltas, sin concepto de cuenta ni de saldo. Un PFM necesita representar ingresos, gastos y transferencias sobre cuentas concretas (banco, efectivo, tarjeta) para poder mostrar saldo, entradas-vs-salidas y evolución. Esta es la base de la que dependen import, presupuestos, dashboard e insights.

## What Changes

- **BREAKING** Se introduce el recurso `accounts` (cuentas del usuario: banco / efectivo / tarjeta / ahorro), con saldo calculado.
- **BREAKING** `Expense` se generaliza a `transactions`: importe **firmado** (negativo = salida, positivo = entrada), `direction` (`income` | `expense` | `transfer`), `account_id`, `posted_at`, `raw_description`, `counterparty`, `source`, `note`, soft-delete (`deleted_at`).
- Transferencias entre cuentas propias: se registran como dos apuntes ligados por `transfer_group_id`. Borrar (soft) cualquiera de las dos patas borra ambas.
- **BREAKING** El JWT pasa a llevar `sub = str(user.id)` en vez del email; `get_current_user` resuelve por id. Invalida las sesiones abiertas al desplegar (sin usuarios en producción).
- Migración de datos: cada `expense` existente pasa a `transaction` con `direction='expense'`, importe negativo y `source='manual'`, asignada a una cuenta `name='Efectivo'`, `type='cash'` creada por usuario.
- Endpoints nuevos: CRUD de `accounts`, CRUD de `transactions` (con filtros y paginación por cursor), `POST /transactions/transfer`, `GET /accounts/{id}/balance` (saldo actual; el saldo a fecha arbitraria lo añadirá `visual-dashboard-and-insights`).
- `PATCH /transactions/{id}` cubre lo que pedía el change `edit-expense`; ese change se archiva como supersedido y no se implementa por separado.
- El endpoint `GET /expenses/summary` se reexpresa sobre `transactions` con filtro por rango de fecha (sin `extract()`), manteniendo el shape de respuesta.
- El frontend `MonthlyExpensesPage` pasa a operar sobre transacciones y muestra un selector de cuenta.

## Capabilities

### New Capabilities
- `accounts`: gestión de las cuentas financieras del usuario (alta, edición, archivado) y cálculo de su saldo a partir del saldo inicial más los movimientos.
- `transactions`: registro y consulta de movimientos (ingreso, gasto, transferencia) asociados a una cuenta, con importe firmado, categoría opcional, pertenencia por usuario y borrado lógico.

### Modified Capabilities

(ninguna con spec previo archivado. El change `edit-expense` no está archivado y no se implementará: su capacidad `expenses` queda subsumida por `transactions`; se archivará como supersedido al aplicar este cambio.)

## Impact

- **Backend**: nuevos `app/models/account.py`, reescritura de `app/models/expense.py` → `transaction.py`; `app/routers/accounts.py`, `app/routers/transactions.py`; `app/schemas/`; migración Alembic con data-migration; `create_access_token` y `get_current_user` pasan a usar `user.id` como `sub`.
- **Frontend**: `features/accounts/` nuevo; `features/expenses/` renombra a `features/transactions/`; `api.ts`, tipos, `MonthlyExpensesPage`, tests.
- **Datos**: tabla `expenses` renombrada/migrada; no reversible sin backup.
- **Dependencias**: sin nuevas.
