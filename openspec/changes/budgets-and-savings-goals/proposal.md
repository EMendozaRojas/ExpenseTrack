## Why

El módulo de diagnóstico y plan de ahorro de la visión necesita dos piezas: **presupuestos** (topes de gasto por categoría con alertas al 80% y 100%) y **metas de ahorro** (objetivos con importe y fecha, y seguimiento del progreso). Sin esto la app solo describe el pasado, no ayuda a planificar.

## What Changes

- Nuevo recurso `budgets`: tope mensual sobre **cualquier categoría de gasto** (raíz o subcategoría), con `amount`, `currency`, `period='monthly'`, `starts_on`, `rollover`, `is_active`. `GET /budgets?month=YYYY-MM` devuelve `{amount, carryover, effective_amount, spent, pct, status}`. `spent` agrega el subárbol de la categoría (raíz + hijas). Cada presupuesto se evalúa independiente (se permite raíz + hija a la vez).
- `rollover` **completo en el MVP**: `effective_amount = amount + carryover`, `carryover = max(0, effective_amount(mes-1) − spent(mes-1))` si `rollover`; el sobregasto no arrastra deuda. `pct`/`status`/alertas contra `effective_amount`.
- Alertas: al cruzar 80% o 100% en un mes, `budget_alert` idempotente (`UNIQUE(budget_id, period_month, threshold)`). Recálculo síncrono al crear/editar/borrar movimientos y en el commit de import; **servicio `scheduler` en docker-compose** (APScheduler) corre `reconcile_budgets` 1×/día como respaldo.
- `GET /budgets/recommendations`: por categoría de gasto, `sugerido = round(media(spent de los 3 meses completos previos con gasto))`, flag `raise`/`lower`/`keep` (banda ±10% vs `amount`) o `create` (categoría sin tope con gasto los 3 meses). Incluye `basis` (los 3 valores + media).
- Nuevo recurso `savings-goals`: meta con `name`, `target_amount`, `target_date`, `current_amount` (= suma de `goal_contributions`), `linked_account_id` opcional **solo informativo**, `status`. `POST /goals/{id}/contributions` registra aportaciones. `GET /goals/{id}/projection` estima la fecha al ritmo de los últimos 3 meses (o "sin ritmo suficiente").

## Capabilities

### New Capabilities
- `budgets`: topes de gasto por categoría y mes, con cálculo de lo gastado, estado (ok / aviso / excedido) y alertas idempotentes al cruzar el 80% y el 100%, más recomendaciones de ajuste basadas en el historial.
- `savings-goals`: metas de ahorro con importe objetivo y fecha, registro de aportaciones y proyección de la fecha de consecución al ritmo actual.

### Modified Capabilities

(ninguna archivada; el recálculo de presupuestos como efecto de cambios en `transactions` y de `statement-import` se especifica aquí.)

## Impact

- **Backend**: `app/models/budget.py`, `app/models/budget_alert.py`, `app/models/savings_goal.py`, `app/models/goal_contribution.py`; `app/routers/budgets.py`, `app/routers/goals.py`; `app/services/budget_calculator.py` (spent/carryover/effective_amount/pct/status/alertas), `app/services/budget_recommender.py`; `app/jobs/scheduler.py` + `app/jobs/reconcile_budgets.py`; hook de recálculo síncrono en el ciclo de vida de `transactions` y en el commit de `imports`.
- **Infra**: nuevo service `scheduler` en `docker-compose.yml` (misma imagen que `backend`, `command: python -m app.jobs.scheduler`).
- **Frontend**: `features/budgets/` (grid mensual con barras 80/100%, tope efectivo + carryover, toggle rollover con aviso), `features/goals/` (progreso, aportar, proyección), cards en el dashboard.
- **Dependencias**: `apscheduler` en `requirements.txt`.
- **Orden**: depende de `accounts-and-transactions` y `hierarchical-categories-and-rules`.
