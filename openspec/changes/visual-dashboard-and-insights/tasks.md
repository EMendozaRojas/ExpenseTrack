<!-- Decisiones D1–D9 resueltas en design.md (revisión 2026-09-04). Recharts, semana ISO, sin MV, recurrentes ±25% bajo demanda, hormiga configurable (default 10€/5/30€), /expenses/summary retirado, savings_rate + over_typical del Apéndice A. Listo para /opsx:apply. -->

## 1. Backend - stats

- [ ] 1.1 `app/services/stats.py`: builders de query agregada por rango y granularidad (`date_trunc`, semana ISO lunes), todo en SQL; tests con datos sintéticos
- [ ] 1.2 `app/routers/stats.py`: `GET /stats/summary` (incl. `savings_rate` + `tier`, null-safe si no hay ingresos), `/stats/by-category`, `/stats/income-vs-expense`, `/stats/balance-trend`, `/stats/top-expenses`; excluir transfers y borrados; agregación por moneda; buckets vacíos a 0; tests de aislamiento y de agregación
- [ ] 1.3 Retirar `GET /expenses/summary`: eliminar el handler en `app/routers/expenses.py` (o el router entero si queda vacío) y sus tests
- [ ] 1.4 Índices `(owner_id, posted_at)` y `(owner_id, category_id, posted_at)` si no existen ya de `accounts-and-transactions`

## 2. Backend - insights

- [ ] 2.1 `app/models/recurring_series.py` (owner_id, counterparty_normalized, status `confirmed`/`dismissed`, cadence, decided_at) + migración
- [ ] 2.2 `app/models/insight_settings.py` (owner_id PK/FK, ant_expense_max_amount default 10.00, ant_expense_min_count default 5, ant_expense_min_aggregate default 30.00, updated_at) + migración
- [ ] 2.3 `app/services/recurring_detector.py`: normaliza contraparte (reusa `normalize()` de `categorizer.py`), agrupa gasto e ingreso, cadencia mensual/semanal/anual con los rangos de gap de D6, tolerancia de importe ±25% de la mediana, mínimo 3 ocurrencias; cálculo bajo demanda sobre 6 meses; tests con series y no-series, incl. ingreso recurrente (nómina)
- [ ] 2.4 `app/services/ant_expense.py`: agrupa por contraparte normalizada bajo el umbral del usuario (de `insight_settings`, con defaults si no existe fila), filtra por `min_count`/`min_aggregate`; en SQL; tests
- [ ] 2.5 `app/services/insights_benchmarks.py`: `share_pct` y `over_typical` (Apéndice A) solo para categorías raíz; tests
- [ ] 2.6 `app/routers/insights.py`: `GET /insights` (top categorías con `share_pct`/`over_typical`), `GET /insights/recurring` + `POST /insights/recurring/{counterparty}/confirm|dismiss`, `GET /insights/ant-expense`, `GET /insights/settings` + `PATCH /insights/settings` (upsert); tests

## 3. Frontend

- [ ] 3.1 Instalar `recharts`; verificar build sin CDN y tema claro/oscuro (guía `dataviz`)
- [ ] 3.2 Selector de rango reutilizable (diario/semanal/mensual/anual/personalizado), opcionalmente sincronizado con la URL
- [ ] 3.3 `features/dashboard/`: tiles (ingresos/gastos/neto/saldo/tasa de ahorro con su `tier`), dona por categoría, barras ingresos-vs-gastos, línea de saldo; estados de carga y vacío
- [ ] 3.4 `features/insights/`: top categorías (resalta `over_typical`), recurrentes (confirmar/descartar, incl. ingresos), gasto hormiga, panel de configuración (editar `ant_expense_max_amount`/`min_count`/`min_aggregate`)
- [ ] 3.5 Reemplazar `MonthlyExpensesPage`/`getMonthlySummary` por los nuevos endpoints de `/stats`; actualizar tests de `features/transactions` afectados

## 4. Verificación

- [ ] 4.1 Backend `ruff`/`mypy`/`pytest --cov` (≥70%); Frontend `eslint`/`tsc`/`vitest --coverage` (≥70%)
- [ ] 4.2 Comprobar que ninguna agregación se hace en Python (revisión de `stats.py`, `ant_expense.py`, `insights_benchmarks.py`)
- [ ] 4.3 Smoke: cargar varios meses de movimientos, revisar las tres gráficas con distintos rangos/granularidades (incl. semana), tile de tasa de ahorro, insights con categoría `over_typical`, recurrentes (gasto e ingreso), cambiar el umbral de hormiga en el panel y ver que el resultado cambia
