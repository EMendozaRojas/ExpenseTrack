## Context

Ver `proposal.md` — Why. Hoy `budgets` tiene una fila por `(owner_id, category_id)` con un `amount` que se aplica a cualquier mes consultado, `is_active` para pausar y borrado físico. `GET /budgets?year=&month=` calcula `spent`/`pct`/`status` al vuelo. Los avisos (`check_budget_notifications` en `app/services/notifications.py`) usan `notifications` con `related_id = budget.id` y `period_key = YYYY-MM`, y solo se disparan al crear/editar movimientos. Borrar una categoría (`DELETE /categories/{id}`) la elimina físicamente y reasigna sus movimientos a "Sin Clasificar". Las categorías no se pueden mover de padre (no hay endpoint de edición).

Decisiones funcionales acordadas con el usuario el 2026-10-05 (conversación previa a este documento): monto propio por mes, "Repetir cada mes" activado por defecto, alcance "Solo este mes" / "Este mes y los siguientes", planificación a futuro, meses pasados de solo lectura con `spent` en vivo, avisos 80/100 solo del mes en curso y revisados al entrar a la app, recomendaciones en el formulario y en una vista aparte, ritmo de gasto solo visual, copiar del mes anterior y resumen de cierre como notificación.

## Goals / Non-Goals

**Goals:**
- Un presupuesto por categoría y mes con monto propio, sin tener que crearlo cada mes.
- Historial fiable: lo presupuestado en meses pasados no cambia por acciones posteriores.
- Avisos al 80% y 100% que no se pierdan, sin infraestructura nueva.
- Ayudas a la planificación baratas: recomendaciones, ritmo, copiar del mes anterior, resumen de cierre.

**Non-Goals:**
- Rollover / acumulación entre meses.
- Multimoneda en presupuestos (D9).
- Totales de montos presupuestados, gráfico histórico, excluir gastos, gastos anuales prorrateados.
- Metas sugeridas y tarjetas del dashboard (`goal-suggestions-dashboard-cards`).
- Scheduler, colas o jobs en segundo plano.

## Decisions

### D1 — Modelo: series + meses explícitos (como eventos repetidos de un calendario)
Materializar una fila por mes no funciona con "repetir indefinidamente". Se usa regla + excepciones:

- **`budgets` = serie** (se conserva la tabla para mantener ids y FKs): `owner_id`, `category_id` (nullable, `ON DELETE SET NULL`), `category_name` (copia del nombre), `amount`, `starts_on` (día 1), `ends_on` (día 1, nullable, exclusivo), `created_at`. Se elimina `is_active` y la unicidad `ux_budgets_owner_category`.
- **`budget_months` = mes explícito**: `owner_id`, `category_id` (nullable, `ON DELETE SET NULL`), `category_name`, `month` (día 1), `kind` (`single` | `override` | `skip`), `amount` (nullable si `skip`), `frozen_spent` (nullable, D8), `created_at`. `UNIQUE(owner_id, category_id, month)`.
  - `single`: presupuesto de un solo mes (no se repite).
  - `override`: monto distinto para un mes dentro de una serie ("Solo este mes", o planificado a mano).
  - `skip`: la serie no aplica ese mes ("Borrar solo este mes").
- **Resolución** del presupuesto de `(categoría C, mes M)`: si hay `budget_months(C, M)` gana (`skip` → no hay presupuesto); si no, la serie de `C` con `starts_on <= M < ends_on` (o `ends_on` nulo); si no, no hay presupuesto.
- **Invariante**: las series de una misma categoría nunca se solapan en el tiempo. Se valida en el servicio (no con constraint de BD: un rango de fechas exclusivo en Postgres necesitaría `btree_gist`, que no compensa a esta escala).
- Respuesta de `GET /budgets?year=&month=`: una entrada por categoría con presupuesto resuelto: `category_id`, `category_name`, `month`, `amount`, `repeats` (true si el mes cae dentro de una serie, aunque tenga `override`), `source` (`series` | `override` | `single`), `editable` (`month >= mes en curso`), `spent`, `pct`, `status` y `pace` (D6).
- Alternativa descartada: una fila por mes generada perezosamente al consultar. Obliga a escribir en un GET, complica "Este mes y los siguientes" (hay que reescribir N filas) y no resuelve meses futuros lejanos.

### D2 — Operaciones
El mes en curso se calcula con `date.today()` del servidor, como hoy. Toda escritura sobre un mes `M < mes en curso` → **409** (meses pasados de solo lectura).

- **Crear** `POST /budgets {category_id, year, month, amount, repeat=true}`: 409 si `(C, M)` ya resuelve a un presupuesto.
  - `repeat=true`: nueva serie desde `M`. Si existe una serie posterior de `C`, la nueva termina donde empieza esa (`ends_on` = su `starts_on`) para no solaparse. Si en `M` hay un `skip`, se elimina.
  - `repeat=false`: `budget_months(kind=single)` (sustituye un `skip` si lo hubiera).
- **Editar** `PUT /budgets/{category_id}/{YYYY-MM} {amount, scope}` con `scope` = `this` | `following`:
  - `single`: `scope` se ignora; se cambia el monto.
  - Dentro de una serie, `this`: upsert `override` en `M`.
  - Dentro de una serie, `following`: la serie actual termina en `M` (`ends_on = M`; si `starts_on == M`, se cambia el monto de la serie y no se divide) y se crea una serie nueva desde `M` con el monto nuevo y el `ends_on` original. Se elimina el `override` de `M` si existía. **Los `override` posteriores a `M` se conservan** (planificados a mano). Un `skip` posterior también se conserva.
- **Borrar** `DELETE /budgets/{category_id}/{YYYY-MM}?scope=this|following`:
  - `single`: se elimina la fila.
  - Dentro de una serie, `this`: upsert `skip` en `M` (sustituye un `override`).
  - Dentro de una serie, `following`: la serie termina en `M` (si `starts_on == M` se elimina la serie) y se eliminan los `budget_months` de `C` posteriores o iguales a `M`. A diferencia de editar, aquí los planificados a mano **no** se conservan: la intención es dejar de presupuestar la categoría. La confirmación los lista.
- **Meses planificados afectados** `GET /budgets/{category_id}/planned?from=YYYY-MM`: devuelve los `override`/`single` de `C` en meses `> from`, para que la UI los mencione en la confirmación ("Diciembre tiene un monto propio (600) y no se cambia" al editar; "También se borrará diciembre (600)" al borrar).
- **Cambiar "Repetir cada mes"** en el formulario de edición: activarlo en un `single` lo convierte en serie desde `M` (misma regla de no solape); desactivarlo en una serie equivale a terminar la serie en `M+1` (el mes `M` se conserva).
- La UI solo pregunta el alcance cuando el presupuesto se repite; en meses pasados no muestra acciones.

### D3 — Avisos 80/100 por categoría y mes
- `check_budget_notifications` evalúa los presupuestos **resueltos para el mes en curso** (D1). `pct >= 100` → `budget_exceeded`; si no, `pct >= 80` → `budget_warning`. Solo esos dos umbrales.
- Clave de unicidad: `(owner_id, type, related_id = category_id, period_key = YYYY-MM)`. Se usa `category_id` en lugar del id de la serie porque el presupuesto de un mes puede venir de una serie, un `override` o un `single`, y "una vez por categoría y mes" es lo que el usuario espera. Si cambia el monto a mitad de mes, los avisos ya creados se conservan y no se repiten.
- Se añade `UNIQUE(owner_id, type, related_id, period_key)` en `notifications`; `_create_if_missing` captura `IntegrityError` como "ya existía" (la revisión al entrar puede coincidir con otras peticiones).
- Disparos síncronos: crear, editar, borrar y restaurar movimiento; bulk-categorize; commit de import (una vez al final); crear, editar y borrar presupuesto; copiar del mes anterior.
- Meses pasados: nunca generan avisos, aunque un import tardío los lleve por encima del 100%. Quedan como `exceeded` en el historial.

### D4 — Revisión al entrar a la app: `POST /notifications/check`
- Endpoint 204 que ejecuta `check_budget_notifications` y `create_month_summary` (D5) para el usuario.
- El frontend lo llama **una vez por carga de la app autenticada** (al montar `AppLayout` tras login o recarga) y luego invalida la query del contador de no leídas.
- Se descarta colgarlo de `GET /auth/me` o `GET /notifications/unread-count`: un GET no debe tener efectos secundarios y `unread-count` va por polling.
- Limitación aceptada: si el usuario no abre la app, no hay avisos ni emails.

### D5 — Resumen de cierre de mes
- En `POST /notifications/check`, si el mes anterior al en curso tuvo al menos un presupuesto resuelto y no existe `budget_month_summary` con `period_key` = ese mes, se crea: "En septiembre cumpliste 4 de 6 presupuestos", y en el cuerpo los excedidos con su `pct`.
- "Cumplido" = `pct < 100`. Los `warning` cuentan como cumplidos.
- `related_id = 0` (no hay entidad asociada). Solo se resume el mes inmediatamente anterior: si el usuario no entra en varios meses, no se generan resúmenes atrasados.
- Se envía también por email cuando está configurado, igual que el resto de notificaciones.

### D6 — Ritmo de gasto (solo visual)
- Solo para el mes en curso: `projected = spent / días transcurridos × días del mes` (días transcurridos incluye hoy).
- `pace = {projected, will_exceed: projected >= amount}`; se devuelve `null` en meses que no son el en curso y durante los primeros 5 días del mes (con tan pocos datos la proyección es ruido).
- No genera notificaciones (decisión del usuario: avisos solo al 80% y 100%).

### D7 — Copiar del mes anterior
- `GET /budgets/copy-preview?year=&month=`: presupuestos `single` del mes anterior a `M` cuya categoría no tiene presupuesto resuelto en `M`. Las series no aparecen porque ya se heredan solas.
- `POST /budgets/copy {year, month, items: [{category_id, amount}]}`: crea `single` en `M` para cada item; 409 si `M` es pasado; los items cuya categoría ya tenga presupuesto en `M` se omiten (nunca pisa) y se informan en la respuesta.
- La UI muestra el botón solo si el preview no está vacío y `M >= mes en curso`; permite desmarcar y editar montos.

### D8 — Categorías borradas: conservar el historial
- Problema: al borrar una categoría, sus movimientos pasan a "Sin Clasificar", así que el `spent` en vivo de los meses pasados caería a 0 y la FK desaparece.
- Solución: antes de borrar la categoría, `DELETE /categories/{id}` llama a `freeze_budgets_for_category`, que para cada mes pasado con presupuesto resuelto de esa categoría (solo la categoría borrada; los presupuestos de sus subcategorías no se tocan) hace upsert de un `budget_months` con el `amount` resuelto y `frozen_spent` = spent calculado en ese momento; termina las series de la categoría en el mes en curso y elimina sus `budget_months` del mes en curso y futuros. `category_name` ya está copiado, y la FK pasa a `NULL` por `ON DELETE SET NULL`.
- Al resolver un mes, si `frozen_spent` no es nulo se usa en lugar de calcular `spent`.
- Se crea una notificación `budget_category_deleted` (`related_id` = id de la categoría borrada, `period_key` vacío) indicando que el presupuesto de esa categoría deja de aplicar y que el historial se conserva.
- Mover una categoría de padre no está soportado hoy (no hay endpoint), así que no se contempla. Si se añade en el futuro, el roll-up de los meses pasados cambiaría en vivo, igual que con una recategorización.
- Excepción al "spent en vivo" (D1): solo los meses congelados por borrado de categoría.

### D9 — Moneda
- Sin cambios respecto al MVP: una sola moneda por usuario (`user_preferences.base_currency`); `spent` suma los importes sin convertir. Si el usuario registra gastos en otra moneda, el `spent` del presupuesto es incorrecto. Limitación conocida; soluciones posibles (filtrar por moneda o convertir con `app/services/fx.py`) quedan para un change propio.

### D10 — Recomendaciones
- `GET /budgets/recommendations?category_id=` (opcional): por categoría de gasto (subárbol para raíces), ventana = 3 meses naturales completos anteriores al en curso; se consideran los meses con `spent > 0`; si son menos de 2, no hay recomendación.
- `suggested = round(media(meses con gasto))`.
- Flag respecto al presupuesto resuelto del **mes en curso**: banda ±10% → `keep`, si no `raise`/`lower`; sin presupuesto y gasto los 3 meses → `create`.
- `basis`: los 3 valores, la media y `same_month_last_year` (spent del mismo mes del año anterior al mes objetivo, o `null` si no hay datos). Es informativo: no cambia `suggested` ni el flag. Solo para raíces de sistema (`is_system`): `share_pct` y `over_typical` con las bandas del Apéndice C de `budgets-and-savings-goals`.
- En el formulario de crear/editar, la UI pide la recomendación de la categoría elegida y ofrece "Usar sugerido". En la vista aparte, acciones "Aplicar sugerido" (editar con `scope=following` en el mes en curso) y "Crear presupuesto" (crear con `repeat=true`).

### D11 — Padre e hija
- Se mantiene: se puede presupuestar una raíz y una de sus hijas a la vez; cada una se evalúa sobre su propio alcance (raíz = subárbol). Ningún cálculo de este change suma montos presupuestados; el resumen de cierre cuenta presupuestos, no montos. Cualquier total futuro deberá evitar la doble cuenta.

## Risks / Trade-offs

- [Lógica de series y excepciones más compleja que una tabla simple] → concentrada en `budget_calculator.py` (resolución) y en un servicio de operaciones con tests por caso (D2); el router queda delgado.
- [El historial "de solo lectura" cambia cuando se corrigen movimientos pasados] → decisión explícita: el tope es fijo y `spent` es en vivo; se explica en la UI de meses pasados.
- [Breaking change en la API de presupuestos] → solo la consume el frontend de este repo; se actualizan juntos.
- [Recalcular presupuestos en cada entrada a la app] → una consulta de `spent` agrupada por categoría para el mes en curso; pocos presupuestos por usuario.
- [Borrar "Este mes y los siguientes" elimina meses planificados] → la confirmación los lista antes de borrar.

## Migration Plan

1. Alembic:
   - `budgets`: añadir `starts_on` (= día 1 del mes de `created_at`), `ends_on` (nullable), `category_name` (copiado de la categoría); `category_id` nullable con `ON DELETE SET NULL`; eliminar `ux_budgets_owner_category`. Los presupuestos con `is_active = false` pasan a `ends_on` = día 1 del mes en curso. Eliminar `is_active`.
   - Crear `budget_months`.
   - `notifications`: para `budget_warning`/`budget_exceeded`, reescribir `related_id` de id de presupuesto a `category_id`; eliminar duplicados (conservando el más antiguo); añadir `UNIQUE(owner_id, type, related_id, period_key)`.
2. Cambio visible: los presupuestos existentes dejan de aparecer en meses anteriores a su creación.
3. Rollback: `downgrade` reconstruye un presupuesto por categoría a partir de la serie vigente en el mes en curso (o la más reciente), restaura `is_active` y la unicidad, y elimina `budget_months`; los montos por mes se pierden.
4. Sin cambios en docker-compose ni en `requirements.txt`.

## Open Questions

(ninguna)
