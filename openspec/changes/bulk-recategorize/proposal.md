<!-- Ficha de idea futura (2026-10-07): solo propuesta. Specs, design y tareas se escriben cuando se decida implementarla. Viene de la tarea 4.3 diferida de `hierarchical-categories-and-rules`. -->

## Why

Después de importar un extracto suele haber muchos movimientos en "Sin Clasificar", y hoy hay que abrirlos y cambiarlos de uno en uno. El backend ya permite cambiar la categoría de varios movimientos a la vez (`POST /transactions/bulk-categorize`), pero la app no lo ofrece.

## What Changes

- En **Movimientos**, un filtro rápido **"Sin clasificar"**.
- **Selección múltiple** de movimientos (casillas y "seleccionar todos los visibles").
- Acción **"Cambiar categoría"** para la selección, que muestra cuántos movimientos cambiaron.
- Los avisos de presupuesto se recalculan después, como ya hace el backend.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `transactions` / `categorization-rules`: añade la recategorización en bloque desde el frontend (el backend ya cumple la spec).

## Impact

- **Frontend**: `features/transactions/` (filtro, selección múltiple y acción en bloque).
- **Backend**: sin cambios previstos.
- **Relación**: complementa `categorization-rules-screen` (crear una regla a partir de la selección sería una mejora natural).
