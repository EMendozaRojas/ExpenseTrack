<!-- Revisado 2026-10-07 antes de archivar: se implementó un dashboard mensual (`GET /dashboard/summary`) e insights más simples que lo planificado. Las specs describen lo implementado; lo demás figura como "Diferido" en tasks.md. -->

## Why

La visión pide un dashboard visual (dona por categoría, barras ingresos-vs-salidas, línea de evolución de saldo) con filtros de fecha, y un módulo de diagnóstico que identifique automáticamente las categorías de mayor impacto, los gastos recurrentes y el "gasto hormiga". Hoy solo existe un `summary` mensual con una tabla y un `CategoryBarChart` básico.

## What Changes

- Nuevo grupo de endpoints `stats`:
  - `GET /stats/summary` — ingresos, gastos, neto, saldo y **`savings_rate` + `tier`**, para un rango.
  - `GET /stats/by-category` — total y porcentaje por categoría de gasto (para la dona).
  - `GET /stats/income-vs-expense` — series por periodo (día/semana ISO/mes/año) para el gráfico de barras.
  - `GET /stats/balance-trend` — saldo acumulado a lo largo del tiempo (línea).
  - `GET /stats/top-expenses` — top N categorías/movimientos por impacto en el rango.
- Nuevo recurso `spending-insights`:
  - Categorías de mayor impacto, con `share_pct` y `over_typical` (solo raíces, frente a las bandas de referencia).
  - Detección de **series recurrentes** (`recurring_series`): agrupación por contraparte normalizada (gasto e ingreso), ≥3 ocurrencias, cadencia con tolerancia de importe **±25%**; cálculo bajo demanda sobre los últimos 6 meses; la tabla solo persiste la decisión confirmar/descartar del usuario.
  - Detección de **gasto hormiga con umbrales configurables por el usuario** (`insight_settings`): por defecto ≤10€/movimiento, ≥5 movimientos, ≥30€ agregado, editables desde un panel en `/insights`.
- Todos los endpoints con filtro de fecha (`date_from`/`date_to`) y granularidad; agregaciones en SQL, no en Python.
- Frontend con **Recharts**: dashboard con las tres gráficas + tiles (incl. tasa de ahorro) + selector de rango (diario/semanal/mensual/anual/personalizado); pantalla `/insights` con top categorías (resaltando `over_typical`), recurrentes, hormiga y su panel de configuración.
- `GET /expenses/summary` **se retira**; el frontend migra a `/stats/summary` + `/stats/by-category`.

## Capabilities

### New Capabilities
- `dashboard-stats`: agregaciones de solo lectura sobre los movimientos del usuario para alimentar el dashboard — resumen ingresos/gastos/neto/saldo/tasa de ahorro, distribución por categoría, comparativa ingresos-vs-gastos por periodo y evolución de saldo, todo filtrable por rango y granularidad.
- `spending-insights`: diagnóstico automático del gasto — categorías de mayor impacto (con señal de gasto por encima de lo típico), detección de pagos recurrentes (con confirmación del usuario) y detección de gasto hormiga con umbrales configurables por el usuario.

### Modified Capabilities

(ninguna archivada. `GET /expenses/summary` se retira, pero nunca se formalizó como `Requirement` en ninguna spec — su retirada es una tarea de implementación, no una entrada `REMOVED`.)

## Impact

- **Backend**: `app/routers/stats.py`, `app/routers/insights.py`; `app/services/stats.py` (queries agregadas parametrizadas), `app/services/recurring_detector.py`, `app/services/ant_expense.py`; `app/models/recurring_series.py`, `app/models/insight_settings.py`; retirada de `app/routers/expenses.py` (ruta `/summary`) y sus tests. Sin vista materializada en este cambio (D5).
- **Frontend**: **Recharts**, `features/dashboard/`, `features/insights/` (incl. panel de configuración de gasto hormiga), selector de rango reutilizable; `MonthlyExpensesPage` migra a `/stats/*`.
- **Dependencias**: `recharts` en `frontend/package.json`; ninguna nueva en backend.
- **Orden**: depende de `accounts-and-transactions` y `hierarchical-categories-and-rules`; se beneficia de `bank-statement-import` (más datos) pero no lo requiere.
