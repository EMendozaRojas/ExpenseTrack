## Why

`budgets-and-savings-goals` se implementó como MVP: un presupuesto es un tope único por categoría que se aplica igual a cualquier mes (también a los anteriores a su creación), borrarlo lo elimina de todo el historial y los avisos solo saltan al crear o editar un movimiento. Eso no sirve para planificar de verdad: el gasto en una categoría cambia de un mes a otro (comida 200 en octubre, 400 en diciembre), el historial de lo presupuestado tiene que ser fiable, y los avisos no pueden depender de qué pantalla se toque.

Este change convierte los presupuestos en **presupuestos mensuales**: cada mes tiene su propio monto por categoría, con la opción de repetirlo automáticamente, y se completa con avisos fiables, recomendaciones basadas en el historial, ritmo de gasto, copia desde el mes anterior y un resumen de cierre de mes.

## What Changes

- **BREAKING (API de presupuestos)**: un presupuesto pasa a identificarse por `(categoría, mes)` en lugar de por un id único. `amount` puede ser distinto cada mes. Desaparece `is_active`.
- **Repetir cada mes** (activado por defecto al crear): el monto se hereda en los meses siguientes hasta que se cambie o se borre. Si está desactivado, el presupuesto existe solo en ese mes.
- **Editar y borrar con alcance**: en un presupuesto que se repite, el usuario elige **"Solo este mes"** o **"Este mes y los siguientes"**. Los meses futuros planificados a mano se respetan al editar; la confirmación los menciona.
- **Planificar a futuro**: se pueden crear y editar presupuestos de meses futuros.
- **Meses pasados de solo lectura**: su tope no se puede cambiar; `spent` se calcula siempre en vivo con los movimientos actuales.
- **Un presupuesto por categoría y mes.** Un presupuesto en una categoría padre y otro en su hija pueden convivir, pero sus montos nunca se suman en un total.
- **Avisos** al 80% (`budget_warning`) y 100% (`budget_exceeded`), solo del mes en curso, uno de cada por categoría y mes. Se evalúan tras cualquier acción que cambie movimientos o presupuestos y **cada vez que el usuario entra a la app** (`POST /notifications/check`). Los meses pasados no generan avisos.
- **Resumen de cierre de mes**: al entrar a la app en un mes nuevo, notificación `budget_month_summary` del mes anterior ("En septiembre cumpliste 4 de 6 presupuestos").
- **Ritmo de gasto** (solo visual, mes en curso): proyección de cierre "a este ritmo acabarás en X".
- **Copiar del mes anterior**: crea en el mes actual o futuro los presupuestos que no se repiten del mes anterior, eligiendo cuáles y ajustando montos; nunca pisa presupuestos existentes.
- **Recomendaciones de tope**: media de los 3 meses completos previos, más el mismo mes del año anterior si hay datos; se muestran al crear/editar un presupuesto y en una vista aparte.
- **Categorías borradas**: los meses pasados conservan el nombre y lo gastado de la categoría; los meses en curso y futuros dejan de aplicar y se avisa al usuario.

### Fuera de alcance

- Rollover / acumulación del sobrante entre meses.
- Multimoneda en presupuestos: `spent` suma importes sin convertir (limitación conocida, ver design D9).
- Total presupuestado del mes frente a ingresos, gráfico histórico por categoría, excluir gastos puntuales, gastos anuales prorrateados (mejoras futuras).
- Metas sugeridas y tarjetas del dashboard: van en `goal-suggestions-dashboard-cards`.
- Servicio `scheduler` / APScheduler: los avisos se evalúan al actuar y al entrar a la app.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `budgets`: pasa de tope único recurrente a presupuestos mensuales con repetición, edición/borrado con alcance, meses pasados de solo lectura, avisos con más disparadores y revisión al acceder, resumen de cierre, ritmo, copia del mes anterior, conservación del historial al borrar categorías y recomendaciones.

## Impact

- **Backend**: `app/models/budget.py` pasa a representar una **serie** (regla que se repite) y se añade `app/models/budget_month.py` (excepciones y presupuestos de un solo mes); migración Alembic con data-migration desde los presupuestos actuales y remapeo de notificaciones; nuevo `app/services/budget_calculator.py` (resolución por mes, spent, pct, status, ritmo); `app/services/budget_recommender.py`; `app/services/notifications.py` (avisos por categoría y mes, resumen de cierre); `app/routers/budgets.py` reescrito; `app/routers/notifications.py` (+`POST /check`); disparos nuevos en `app/routers/transactions.py` e `app/routers/imports.py`; `app/routers/categories.py` (congelar historial al borrar).
- **Frontend**: `features/budgets/` (formulario con "Repetir cada mes" y recomendación, diálogo de alcance, meses pasados en solo lectura, ritmo, copiar del mes anterior, vista de recomendaciones); `AppLayout` (llamada a `POST /notifications/check` al entrar); `features/notifications/` (render del resumen y del aviso de categoría borrada).
- **Infra / dependencias**: sin cambios.
- **Relación con otros changes**: depende de `budgets-and-savings-goals` (archivado antes que este). `goal-suggestions-dashboard-cards` va después y usa el modelo de este change. Con presupuestos por mes, el formulario en la página de `create-button-modal-budgets-goals` aparece en los meses sin presupuestos (la condición de la UI no cambia).
