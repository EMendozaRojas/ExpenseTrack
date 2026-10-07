<!-- Ficha de idea futura (2026-10-07): solo propuesta, no se implementa durante el MVP. Specs, design y tareas se escriben cuando se decida implementarla. -->

## Why

Un presupuesto suma el gasto de su categoría en todas las cuentas, que es lo correcto: "¿cuánto gasto en Comida al mes?" no depende de con qué se pague. Pero el usuario no puede ver desde dónde sale ese gasto. Filtrar los presupuestos por cuenta falsearía el porcentaje (compararía una parte del gasto contra el tope completo), así que la alternativa es mostrar el reparto sin cambiar el total.

## What Changes

- En cada presupuesto, un **detalle del gasto por cuenta**: por ejemplo, "Comida 280 € de 300 €: 200 € tarjeta, 80 € efectivo".
- El total, el porcentaje, el estado y los avisos **no cambian**: siguen contando todas las cuentas.
- Solo se muestra el detalle cuando el gasto viene de más de una cuenta.

### Fuera de alcance

- Presupuestos distintos por cuenta (otro modelo de presupuesto; descartado para el MVP).
- Desplegable de cuenta en Presupuestos y Metas (las metas no dependen de las cuentas).

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `budgets`: el estado de cada presupuesto incluye el gasto desglosado por cuenta.

## Impact

- **Backend**: `services/budget_calculator.py` (agrupar también por cuenta), `schemas/budget.py` (campo con el desglose), `openapi.json` regenerado.
- **Frontend**: `features/budgets/components/BudgetCard.tsx` (mostrar el desglose).
- **Relación**: tiene sentido después de `accounts-screen` (hoy el usuario no puede crear una segunda cuenta). Si se implementa `independent-currency-accounts`, solo entran las cuentas en la moneda principal.
