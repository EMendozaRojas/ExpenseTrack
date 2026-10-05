<!-- Revisado 2026-10-05: tareas recortadas al MVP implementado y marcadas como hechas. Lo no implementado figura en "Diferido" y pasa a `monthly-budgets-planning` (presupuestos) y `goal-suggestions-dashboard-cards` (metas sugeridas y dashboard). -->

## 1. Modelo y migración

- [x] 1.1 `app/models/budget.py` (owner_id, category_id, amount, is_active, created_at); unicidad por `(owner_id, category_id)` comprobada en el endpoint
- [x] 1.2 `app/models/savings_goal.py` (owner_id, name, target_amount, target_date, linked_account_id nullable, status `active`/`completed`/`archived`) y `app/models/goal_contribution.py` (goal_id, amount, contributed_at, note)
- [x] 1.3 Migraciones Alembic `budgets` y `savings_goals` (incluye `goal_contributions`); sin data-migration

## 2. Cálculo y avisos de presupuestos

- [x] 2.1 `spent(budget, mes)` sobre el subárbol de la categoría (raíz + hijas; subcategoría = solo ella), excluye borrados y no-gastos; test de roll-up y de independencia raíz/subcategoría
- [x] 2.2 `pct` y `status` (`ok`/`warning`/`exceeded`) contra `amount`; test de los cortes 80/100
- [x] 2.3 `check_budget_notifications` en `app/services/notifications.py`: notificación `budget_warning`/`budget_exceeded` única por `(presupuesto, tipo, mes)`, llamada tras crear y editar movimientos

## 3. API

- [x] 3.1 `app/routers/budgets.py`: CRUD (rechaza categoría no-gasto / no visible / duplicada / importe ≤ 0) + `GET /budgets?year=&month=` con `spent`/`pct`/`status`; tests de aislamiento
- [x] 3.2 `app/routers/goals.py`: CRUD (cuenta vinculada debe ser del usuario) + `POST/GET/DELETE /goals/{id}/contributions` + `GET /goals/{id}/projection`; avisos `goal_near`/`goal_reached`; tests (aportación avanza `current_amount`, meta pasa a `completed`, proyección con ritmo, sin datos y ya completada, aislamiento)

## 4. Frontend

- [x] 4.1 `features/budgets/`: lista mensual por categoría con barra y estado 80/100%, crear, editar importe y borrar
- [x] 4.2 `features/goals/`: progreso, aportar, ver proyección, crear y borrar

## Diferido a `monthly-budgets-planning` (presupuestos) y `goal-suggestions-dashboard-cards` (metas sugeridas y dashboard)

> Nota: al revisar lo diferido se descartaron el rollover (`carryover`/`effective_amount`), la tabla `budget_alert` y el servicio `scheduler`, y los presupuestos pasan a tener un monto por mes. Ver el design de `monthly-budgets-planning`.

- `currency`, `period`, `starts_on`, `rollover` en `budgets`; `carryover`/`effective_amount` (D2, D3)
- Tabla `budget_alert` con `UNIQUE(budget_id, period_month, threshold)`; avisos también al borrar movimientos y en el commit de `imports`
- `app/jobs/reconcile_budgets.py`, `app/jobs/scheduler.py` (APScheduler) y service `scheduler` en `docker-compose.yml` (D4)
- `app/services/budget_recommender.py` + `GET /budgets/recommendations` + vista de recomendaciones con `basis` (D6)
- Presets de metas "Fondo de emergencia" e "Independencia financiera" (D9)
- Cards de presupuestos y metas en el dashboard
- Verificación: `ruff`/`mypy`/`pytest --cov` (≥70%), `eslint`/`tsc`/`vitest --coverage` (≥70%) y smoke test completo
