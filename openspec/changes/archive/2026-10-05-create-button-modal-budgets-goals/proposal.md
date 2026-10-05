<!-- Change documentado a posteriori: ya implementado en el commit 8fa949b (2026-10-05). -->

## Why

En `/budgets` y `/goals` el formulario de creación estaba siempre visible encima de la lista, ocupando espacio aunque el usuario ya tuviera registros. En Movimientos ya se resolvió con un patrón distinto: formulario en la página solo mientras no hay datos y, después, un botón arriba a la derecha que lo abre en un modal. Unificar las tres pantallas da una UX coherente y deja la lista como protagonista cuando ya hay contenido.

## What Changes

- `/budgets`: si el usuario **no** tiene presupuestos, el formulario "Nuevo presupuesto" se muestra en la página. Si tiene al menos uno (los presupuestos son recurrentes, así que aparecen en todos los meses), el formulario se oculta y aparece el botón **"+ Nuevo presupuesto"** en la barra superior, a la derecha del selector de mes, que abre el formulario en un `Modal`.
- `/goals`: si el usuario **no** tiene metas, el formulario "Nueva meta de ahorro" se muestra en la página. Si tiene metas, se oculta y aparece el botón **"+ Nueva meta"** arriba a la derecha, que abre el formulario en un `Modal`.
- En ambos casos el modal se cierra al crear el registro con éxito; si hay error, permanece abierto mostrando el mensaje.
- Mientras la lista está cargando no se muestra ni el formulario ni el botón.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `budgets`: comportamiento de la UI de creación de presupuestos (formulario en la página vs. botón + modal según el usuario tenga o no presupuestos).
- `savings-goals`: comportamiento de la UI de creación de metas (formulario en la página vs. botón + modal según haya metas).

## Impact

- **Frontend**: `features/budgets/BudgetsPage.tsx`, `features/goals/GoalsPage.tsx` (reutilizan `components/Modal`), `index.css` (nueva clase `.expenses-toolbar-end`), tests de ambas páginas.
- **Backend**: sin cambios. **API**: sin cambios.
