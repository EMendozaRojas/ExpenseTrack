## Why

Dos piezas que quedaron fuera de `budgets-and-savings-goals` y se separaron de `monthly-budgets-planning` para que cada change sea pequeño y se cierre por separado. Crear una meta de ahorro hoy obliga a inventarse el importe; marcos de referencia como el fondo de emergencia o la independencia financiera, calculados con el gasto real, dan un punto de partida razonable. Y el dashboard, que es la pantalla de entrada, no muestra ni presupuestos ni metas, así que para saber cómo va el mes hay que ir a cada página.

## What Changes

- **Presets de metas**: `GET /goals/suggestions` devuelve "Fondo de emergencia" (6 × gasto mensual medio, con meses de cobertura actuales y su tramo) e "Independencia financiera" (25 × gasto anual). El formulario de crear meta permite partir de ellos con nombre e importe editables.
- **Dashboard**: tarjeta de presupuestos (los que están en aviso o excedidos en el mes seleccionado) y tarjeta de metas activas (progreso).

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `savings-goals`: añade metas sugeridas (presets) a partir del gasto real.
- `dashboard-stats`: añade tarjetas de presupuestos y metas al dashboard.

## Impact

- **Backend**: `app/routers/goals.py` (+`GET /goals/suggestions`), reusando el cálculo de saldos de cuentas existente.
- **Frontend**: `features/goals/` (selector de sugerencias en el formulario de crear meta), `features/dashboard/` (tarjetas).
- **Infra / dependencias**: sin cambios.
- **Orden**: se implementa **después** de `monthly-budgets-planning`: la tarjeta de presupuestos usa el modelo de presupuestos por mes (`GET /budgets?year=&month=` con `amount` del mes).
