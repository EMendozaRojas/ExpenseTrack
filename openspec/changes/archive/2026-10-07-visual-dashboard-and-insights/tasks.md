<!-- Revisado 2026-10-07 antes de archivar: se implementó una versión mensual más simple que la planificada (commits 63712d1, 050848e, f337805 y c7608ee). Las tareas reflejan lo implementado; el plan original figura en "Diferido". -->

## 1. Backend - dashboard

- [x] 1.1 `GET /dashboard/summary?year=&month=&account_id=`: ingresos, gastos, neto con `net_status`, fijos/variables, gasto por categoría en árbol y aviso de datos incompletos; sin transferencias ni borrados, agregado en SQL; tests de aislamiento y de agregación

## 2. Backend - insights

- [x] 2.1 `app/services/recurring_detector.py`: series recurrentes de gasto e ingreso por contraparte normalizada, ≥3 ocurrencias, ±25% de la media, cadencia regular; bajo demanda sobre ~6 meses; tests
- [x] 2.2 `app/models/dismissed_recurring_series.py` + `GET /insights/recurring`, `POST /insights/recurring/dismiss` y `/restore`; tests
- [x] 2.3 Gasto hormiga por subcategoría con umbrales configurables (`GET /insights/ant-spending`); tests
- [x] 2.4 Umbrales en `user_preferences` (fusionados desde `insight_settings`, commit f337805) con `GET`/`PATCH /insights/settings`; tests

## 3. Frontend

- [x] 3.1 `features/dashboard/`: tarjetas de ingresos, gastos y neto, dona por categoría y barras de entradas frente a salidas (componentes propios, sin Recharts), mes y cuenta sincronizados con la URL
- [x] 3.2 `features/insights/`: recurrentes (descartar/recuperar), gasto hormiga y panel de umbrales

## Diferido

Del plan original, no implementado:

- Endpoints `/stats/summary`, `/stats/by-category`, `/stats/income-vs-expense`, `/stats/balance-trend` y `/stats/top-expenses` con rangos arbitrarios y granularidad diaria/semanal/mensual/anual
- Tasa de ahorro (`savings_rate`) con su tramo y saldo en el tiempo
- Selector de rango reutilizable (diario/semanal/anual/personalizado) y Recharts
- `GET /insights` con top categorías, `share_pct` y `over_typical` (el `share_pct`/`over_typical` se calcula hoy en las recomendaciones de presupuestos)
- Confirmar series recurrentes (solo se pueden descartar); detección por contraparte del gasto hormiga
- Retirar `GET /expenses/summary` (se mantiene; ver el design D8 de `api-documentation`)
- Verificación de que ninguna agregación se hace en Python; smoke del plan original
