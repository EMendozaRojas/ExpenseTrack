<!-- Ficha de idea futura (2026-10-12): solo propuesta, no se implementa durante el MVP. Specs, design y tareas se escriben cuando se decida implementarla. -->

## Why

La revisión técnica del 2026-10-11 señala que `routers/transactions.py` tiene más de 500 líneas con lógica de negocio (autocategorización, cursores de paginación, transferencias), aunque el README dice que la arquitectura es «routers → services».

## What Changes

- Mover la lógica a `services/transactions.py` y dejar el router en recibir la petición, llamar al servicio y devolver la respuesta. Sin cambios de comportamiento: los tests actuales deben pasar igual.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

(ninguna: es una reorganización interna)

## Impact

- **Backend**: `routers/transactions.py` y nuevo `services/transactions.py`.
