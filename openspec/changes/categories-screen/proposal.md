<!-- Ficha de idea futura (2026-10-07): solo propuesta. Specs, design y tareas se escriben cuando se decida implementarla. Viene de la tarea 4.1 diferida de `hierarchical-categories-and-rules`. -->

## Why

Hoy las categorías solo aparecen como una lista desplegable al registrar un movimiento. No hay ningún sitio en la app para verlas en árbol, crear las propias, cambiarles el icono o el color, marcar cuáles son gastos fijos ni borrarlas, aunque el backend ya lo permite (`/categories`). Para personalizar la app hay que usar la API.

## What Changes

- Nueva pantalla **Categorías** (en el menú o dentro de Configuración) con el árbol de categorías de gasto e ingreso: las de sistema y las propias.
- Crear una categoría raíz o una subcategoría, con nombre, icono, color y "gasto fijo".
- Borrar una categoría propia, avisando antes de qué pasará: cuántos movimientos pasan a "Sin Clasificar", qué subcategorías suben de nivel y que los presupuestos conservan su historial.
- Las categorías de sistema se muestran pero no se pueden borrar.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `categories`: añade la gestión de categorías desde el frontend. Puede requerir un endpoint para editar nombre, icono, color o "gasto fijo", que hoy no existe.

## Impact

- **Frontend**: nuevo `features/categories/`, entrada en el menú o en Configuración.
- **Backend**: posiblemente `PATCH /categories/{id}` para editar (hoy solo hay crear, listar y borrar) y un aviso previo con el número de movimientos afectados.
- **Relación**: complementa `categorization-rules-screen` y `bulk-recategorize`.
