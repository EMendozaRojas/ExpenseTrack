<!-- Decisiones D1–D8 resueltas en design.md (revisión 2026-09-02). Presupuesto en cualquier nivel, rollover completo, servicio scheduler en compose, recomendación media 3m + banda 10% + create. Listo para /opsx:apply. -->

## 1. Modelo y migración

- [ ] 1.1 `app/models/budget.py` (owner_id, category_id, amount, currency, period, starts_on, rollover, is_active, created_at, updated_at) + `UNIQUE(owner_id, category_id, period, starts_on)` para activos
- [ ] 1.2 `app/models/budget_alert.py` (budget_id, threshold, period_month, spent_amount, effective_amount, triggered_at) + `UNIQUE(budget_id, period_month, threshold)`
- [ ] 1.3 `app/models/savings_goal.py` (owner_id, name, target_amount, target_date, linked_account_id nullable, status) y `app/models/goal_contribution.py` (goal_id, amount, contributed_on, transaction_id nullable)
- [ ] 1.4 Migración Alembic de las cuatro tablas; sin data-migration; verificar `upgrade`/`downgrade` en base de prueba

## 2. Cálculo de presupuestos

- [ ] 2.1 `app/services/budget_calculator.py`: `spent(budget, mes)` sobre el subárbol de la categoría (raíz + hijas; subcategoría = solo ella), excluye transfers, borrados y otra moneda; tests
- [ ] 2.2 `carryover(budget, mes)` y `effective_amount` con recursión desde `starts_on`, `max(0, …)`, memoización por `(budget_id, mes)`; tests: sobrante rueda, sobregasto no crea deuda, `rollover` off → siempre `amount`, `starts_on` como reset
- [ ] 2.3 `pct` y `status` (`ok`/`warning`/`exceeded`) contra `effective_amount`; tests de los cortes 80/100
- [ ] 2.4 Disparo de alertas idempotente al cruzar 80/100% (sobre `effective_amount`); test "una sola alerta por (budget, mes, threshold)"
- [ ] 2.5 Hook de recálculo síncrono en crear/editar/borrar `transaction` y en el commit de `imports`: una pasada por `(presupuesto afectado, mes)` distinto, no por movimiento; tests

## 3. Job scheduler

- [ ] 3.1 `app/jobs/reconcile_budgets.py`: recorre presupuestos activos del mes en curso, recalcula, crea las alertas que falten (idempotente); ejecutable como `python -m app.jobs.reconcile_budgets`; test del comando contra datos sembrados
- [ ] 3.2 `app/jobs/scheduler.py`: `BlockingScheduler` de APScheduler, job diario 03:00 → `reconcile_budgets`; `apscheduler` en `requirements.txt`
- [ ] 3.3 Service `scheduler` en `docker-compose.yml` (imagen de `backend`, `command: python -m app.jobs.scheduler`, `env_file`, `depends_on: db`); verificar que `docker compose up` levanta los tres servicios

## 4. Recomendaciones

- [ ] 4.1 `app/services/budget_recommender.py`: ventana = 3 meses completos previos; `meses_con_gasto`; `sugerido = round(media(meses_con_gasto))`; flag `raise`/`lower`/`keep` (banda ±10% vs `amount`) para categorías con presupuesto, `create` para categorías sin presupuesto con gasto los 3 meses; `basis` con los 3 valores + media; tests con historial sintético (ajustar, crear, historia insuficiente)
- [ ] 4.2 `basis` incluye `share_pct` (share de la categoría raíz sobre el gasto total del rango) y `over_typical` según las bandas del Apéndice C (Vivienda >35, Transporte >20, Alimentación >15); solo para categorías raíz; test de que `over_typical` no cambia el flag principal

## 5. API

- [ ] 5.1 `app/routers/budgets.py`: CRUD (rechaza categoría no-gasto / no visible / duplicado activo) + `GET /budgets?month=YYYY-MM` (`amount`/`carryover`/`effective_amount`/`spent`/`pct`/`status`) + `GET /budgets/alerts?since=` + `GET /budgets/recommendations`; tests de aislamiento
- [ ] 5.2 `app/routers/goals.py`: CRUD + `POST /goals/{id}/contributions` + `GET /goals/{id}/projection`; tests (aportación avanza `current_amount`, meta pasa a `reached`, proyección con ritmo y sin ritmo suficiente, `linked_account_id` no deriva saldo)

## 6. Frontend

- [ ] 6.1 `features/budgets/`: grid mensual por categoría con barra y estado 80/100% sobre el tope efectivo, muestra `carryover`; modal set tope + toggle `rollover` con aviso de "acredita infragasto retroactivo; mueve la fecha de inicio para resetear"
- [ ] 6.2 Vista de recomendaciones con el `basis` visible (3 meses + media) y acción rápida "aplicar sugerido" / "crear presupuesto"
- [ ] 6.3 `features/goals/`: progreso, aportar, proyección; flujo "crear meta" con presets D9 calculados desde `/stats` — "Fondo de emergencia" (`6 × media gasto mensual 3m`, muestra meses de cobertura y su tramo) e "Independencia financiera" (`25 × gasto anual`); importes editables
- [ ] 6.4 Cards de presupuestos (alertas del mes) y metas en el dashboard; tests

## 7. Verificación

- [ ] 7.1 Backend `ruff`/`mypy`/`pytest --cov` (≥70%); Frontend `eslint`/`tsc`/`vitest --coverage` (≥70%)
- [ ] 7.2 Smoke: crear presupuesto con rollover, gastar por debajo un mes y ver el tope efectivo del siguiente; llegar al 80% y 100% y verificar alertas únicas; importar un extracto que cruce el umbral y ver la alerta creada en el commit; parar el `scheduler`, provocar un desfase y comprobar que `reconcile_budgets` lo arregla; crear meta, aportar 3 meses, ver proyección
