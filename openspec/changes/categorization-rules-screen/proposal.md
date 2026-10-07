<!-- Ficha de idea futura (2026-10-07): solo propuesta. Specs, design y tareas se escriben cuando se decida implementarla. Viene de la tarea 4.2 diferida de `hierarchical-categories-and-rules`. -->

## Why

Las reglas de categorización (por ejemplo, "todo lo que contenga MERCADONA va a Supermercado") ya funcionan en el backend y se aplican al registrar e importar movimientos, pero no hay ninguna pantalla para crearlas, verlas ni aplicarlas. Sin ellas, cada movimiento importado que no reconocen las reglas de sistema acaba en "Sin Clasificar" y hay que corregirlo a mano.

## What Changes

- Nueva pantalla **Reglas** con la lista de reglas propias (patrón, tipo de coincidencia, categoría, prioridad, activa/inactiva).
- Crear, editar, activar/desactivar y borrar reglas.
- Antes de guardar, **probar el patrón**: cuántos movimientos coincidirían (`GET /categorization-rules/preview`).
- **Aplicar una regla** a los movimientos que están en "Sin Clasificar" (`POST /categorization-rules/{id}/apply`) y ver cuántos cambiaron.
- Opcional: al categorizar un movimiento a mano, ofrecer "crear una regla para este comercio".

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `categorization-rules`: añade la gestión de reglas desde el frontend (el backend ya cumple la spec).

## Impact

- **Frontend**: nuevo `features/rules/` (o dentro de Configuración); posible acceso directo desde Movimientos.
- **Backend**: sin cambios previstos.
- **Relación**: complementa `categories-screen` y `bulk-recategorize`.
