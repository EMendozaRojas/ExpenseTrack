<!-- Revisado 2026-10-05: alcance recortado a lo realmente implementado (MVP). Lo no implementado se difiere a `monthly-budgets-planning` (presupuestos) y `goal-suggestions-dashboard-cards` (metas sugeridas y dashboard). -->

## Why

El módulo de diagnóstico y plan de ahorro de la visión necesita dos piezas: **presupuestos** (topes de gasto por categoría con avisos al 80% y 100%) y **metas de ahorro** (objetivos con importe y fecha, y seguimiento del progreso). Sin esto la app solo describe el pasado, no ayuda a planificar.

## What Changes

- Nuevo recurso `budgets`: tope mensual recurrente sobre **cualquier categoría de gasto** visible (raíz o subcategoría), con `amount` e `is_active`. Como máximo un presupuesto por categoría y usuario. `GET /budgets?year=&month=` devuelve cada presupuesto con `spent`, `pct` y `status` (`ok`/`warning`/`exceeded`) calculados al vuelo para ese mes. `spent` agrega el subárbol de la categoría (raíz + hijas). Cada presupuesto se evalúa de forma independiente.
- Avisos de presupuesto mediante el sistema de notificaciones: al crear o editar un movimiento, si un presupuesto activo cruza el 80% o el 100% en el mes en curso, se crea una notificación `budget_warning` / `budget_exceeded` (una por presupuesto, tipo y mes).
- Nuevo recurso `savings-goals`: meta con `name`, `target_amount`, `target_date` opcional, `linked_account_id` opcional **solo informativo** y `status` (`active`/`completed`/`archived`). `current_amount` = suma de aportaciones. `POST/GET/DELETE /goals/{id}/contributions` gestiona aportaciones; al alcanzar el objetivo la meta pasa a `completed`. `GET /goals/{id}/projection` estima la fecha al ritmo de los últimos 3 meses completos (o "sin datos suficientes"). Avisos `goal_near` (80%) y `goal_reached` (100%).
- Frontend: páginas `/budgets` (lista mensual con barra y estado, crear/editar importe/borrar) y `/goals` (progreso, aportar, proyección, borrar).

### Diferido a `monthly-budgets-planning` (presupuestos) y `goal-suggestions-dashboard-cards` (metas sugeridas y dashboard)

> Nota: al revisar lo diferido se descartaron el rollover (`carryover`/`effective_amount`), la tabla `budget_alert` y el servicio `scheduler`, y los presupuestos pasan a tener un monto por mes. Ver el design de `monthly-budgets-planning`.

- `rollover`/`carryover`/`effective_amount` y los campos `currency`, `period`, `starts_on` del presupuesto.
- Tabla `budget_alert` con alertas idempotentes por `(budget, mes, threshold)`.
- Recálculo de avisos al borrar movimientos y en el commit de imports.
- Job `reconcile_budgets` + servicio `scheduler` (APScheduler) en docker-compose.
- `GET /budgets/recommendations` y su vista.
- Presets de metas (Fondo de emergencia, Independencia financiera).
- Cards de presupuestos y metas en el dashboard.
- Verificación de cobertura ≥70% y smoke test completo.

## Capabilities

### New Capabilities
- `budgets`: topes de gasto mensuales por categoría, con cálculo de lo gastado en el mes, estado (ok / aviso / excedido) y avisos al cruzar el 80% y el 100%.
- `savings-goals`: metas de ahorro con importe objetivo y fecha, registro de aportaciones, paso a completada y proyección de la fecha de consecución al ritmo actual.

### Modified Capabilities

(ninguna archivada; el disparo de avisos de presupuesto desde `transactions` se especifica aquí.)

## Impact

- **Backend**: `app/models/budget.py`, `app/models/savings_goal.py`, `app/models/goal_contribution.py`; `app/routers/budgets.py`, `app/routers/goals.py`; `app/services/notifications.py` (avisos de presupuesto y meta); llamada a `check_budget_notifications` en crear/editar de `app/routers/transactions.py`; migraciones `budgets` y `savings_goals`.
- **Frontend**: `features/budgets/`, `features/goals/`.
- **Dependencias**: ninguna nueva.
- **Orden**: depende de `accounts-and-transactions` y `hierarchical-categories-and-rules`. El sistema de notificaciones (`app/models/notification.py`) se usa como canal de avisos.
