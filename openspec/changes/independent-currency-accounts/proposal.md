<!-- Ficha de idea futura (2026-10-07): solo propuesta, no se implementa durante el MVP. Specs, design y tareas se escriben cuando se decida implementarla. Decisiones ya tomadas con el usuario: puntos 1–3 de "What Changes". -->

## Why

La idea de multimoneda es tener **cuentas independientes en distintas monedas**: por ejemplo, la cuenta principal en euros y otra cuenta en EE. UU. en dólares, sin ninguna relación entre ellas. No se quiere convertir importes ni registrar en una cuenta movimientos en otra moneda.

Hoy la API permite registrar un movimiento en una moneda distinta a la de su cuenta, convirtiéndolo con un tipo de cambio cargado a mano. La app no lo usa (el formulario no lo ofrece y no hay datos así), pero esa vía sobra y además tiene un fallo: el saldo de la cuenta suma el importe original sin convertir. Y en cuanto exista una cuenta en otra moneda, el dashboard con "todas las cuentas" y los presupuestos sumarían euros y dólares como si fueran lo mismo.

## What Changes

1. **Un movimiento siempre está en la moneda de su cuenta.** Se elimina de la API la opción de registrar un movimiento en otra moneda (`currency` al crear un movimiento) y los tipos de cambio (`/fx-rates` y `app/services/fx.py`). Con eso desaparece también el fallo del saldo.
2. **Dashboard con "todas las cuentas": totales separados por moneda.** Ingresos, gastos, neto y gasto por categoría se muestran en un bloque por cada moneda (euros, dólares…), sin sumarlos entre sí. Al filtrar por una cuenta se ve solo su moneda.
3. **Presupuestos y metas solo cuentan las cuentas en la moneda principal.** El gasto de una cuenta en otra moneda no entra en los presupuestos (que se expresan en la moneda principal). Ese gasto se consulta en el dashboard filtrando por esa cuenta.

### Fuera de alcance

- Conversión entre monedas de cualquier tipo.
- Transferencias entre cuentas de distinta moneda (no es una idea prevista).

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `multi-currency`: deja de convertir; cada cuenta tiene su moneda y sus movimientos están siempre en ella. Se eliminan los tipos de cambio.
- `transactions`: el movimiento hereda la moneda de su cuenta; se quita el campo `currency` de la entrada.
- `dashboard-stats`: con todas las cuentas, totales y desglose por moneda.
- `budgets`: solo cuentan los movimientos de cuentas en la moneda principal.

## Impact

- **Backend**: `routers/transactions.py`, `schemas/transaction.py`, eliminar `routers/fx_rates.py`, `models/fx_rate.py`, `services/fx.py` (migración para borrar la tabla `fx_rates`, hoy vacía); `routers/dashboard.py` y `schemas/dashboard.py` (agrupación por moneda); `services/budget_calculator.py` y `budget_recommender.py` (filtrar por moneda principal); regenerar `openapi.json`.
- **Frontend**: `features/dashboard/` (bloques por moneda).
- **Datos**: sin impacto hoy (todas las cuentas están en euros y no hay movimientos en otra moneda ni tipos de cambio cargados, comprobado el 2026-10-07).
- **Relación**: puede afectar a `goal-suggestions-dashboard-cards` (tarjetas del dashboard) si se implementa antes.
