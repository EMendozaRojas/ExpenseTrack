## 1. Modelo y migración

- [ ] 1.1 `app/models/budget.py` como serie (`starts_on`, `ends_on`, `category_name`, `category_id` nullable `ON DELETE SET NULL`, sin `is_active`) y nuevo `app/models/budget_month.py` (`month`, `kind` single/override/skip, `amount`, `frozen_spent`, `category_name`, `UNIQUE(owner_id, category_id, month)`) según D1
- [ ] 1.2 Migración Alembic según el Migration Plan: data-migration de presupuestos existentes (incl. inactivos → `ends_on`), crear `budget_months`, remapear `related_id` de avisos de presupuesto a `category_id`, deduplicar y `UNIQUE(owner_id, type, related_id, period_key)` en `notifications`; verificar `upgrade`/`downgrade`

## 2. Resolución y cálculo

- [ ] 2.1 `app/services/budget_calculator.py`: resolver el presupuesto de `(categoría, mes)` (override/single/skip > serie > nada) y de todas las categorías de un mes; tests de cada caso de resolución
- [ ] 2.2 `spent` por subárbol y mes (una consulta agrupada), uso de `frozen_spent` cuando existe, `pct`, `status`; tests (roll-up, cortes 80/100, cada mes empieza en 0, corrección tardía visible en mes pasado)
- [ ] 2.3 `pace` según D6; tests (proyección, `will_exceed`, null en otros meses y en los 5 primeros días)
- [ ] 2.4 Sustituir `_spent_for_category` duplicado en `routers/budgets.py` y `services/notifications.py` por el calculador

## 3. Operaciones sobre presupuestos

- [ ] 3.1 Servicio de operaciones: crear (serie sin solape / single), editar `this`/`following`, borrar `this`/`following`, activar/desactivar repetir, rechazo de meses pasados; tests por cada escenario del spec (incl. planificados conservados al editar y borrados al borrar `following`)
- [ ] 3.2 `app/routers/budgets.py`: `GET /budgets?year=&month=`, `POST /budgets`, `PUT` y `DELETE /budgets/{category_id}/{YYYY-MM}`, `GET /budgets/{category_id}/planned?from=`; validaciones (categoría de gasto visible, `amount > 0`, conflicto por mes); tests de aislamiento entre usuarios
- [ ] 3.3 `GET /budgets/copy-preview` y `POST /budgets/copy` según D7; tests (solo single, nunca pisa, mes pasado → 409)

## 4. Avisos y notificaciones

- [ ] 4.1 `check_budget_notifications` sobre presupuestos resueltos del mes en curso, clave `related_id = category_id`; `_create_if_missing` captura `IntegrityError`; tests (una vez por categoría y mes aunque cambie el monto, meses pasados sin avisos)
- [ ] 4.2 Disparos nuevos: borrar y restaurar movimiento, bulk-categorize, crear/editar/borrar presupuesto, copiar; tests
- [ ] 4.3 Disparo al final de `POST /imports/{id}/commit` (una vez por commit); test con un import que cruza el 80%
- [ ] 4.4 `create_month_summary` (D5); tests (resumen con excedidos, solo una vez, sin presupuestos el mes anterior → nada)
- [ ] 4.5 `POST /notifications/check` (204) que ejecuta 4.1 y 4.4; test "aviso perdido se crea al entrar, sin duplicar"
- [ ] 4.6 `freeze_budgets_for_category` en `DELETE /categories/{id}` + notificación `budget_category_deleted` (D8); tests (historial conservado con `frozen_spent`, nada desde el mes en curso)

## 5. Recomendaciones

- [ ] 5.1 `app/services/budget_recommender.py` + `GET /budgets/recommendations?category_id=` según D10 (incl. `same_month_last_year`; `share_pct`/`over_typical` solo en raíces de sistema); tests: subir, mantener, crear, historia insuficiente, referencia estacional no cambia el flag

## 6. Frontend

- [ ] 6.1 `features/budgets/api.ts` y tipos para la nueva API
- [ ] 6.2 Formulario crear/editar: "Repetir cada mes" (activado por defecto), recomendación de la categoría elegida con "Usar sugerido"
- [ ] 6.3 Diálogo de alcance "Solo este mes" / "Este mes y los siguientes" al editar y borrar un presupuesto que se repite, mencionando los meses planificados afectados
- [ ] 6.4 Meses pasados en solo lectura (sin acciones ni formulario/botón de crear, nota "lo gastado refleja tus movimientos actuales"); navegación a meses futuros para planificar
- [ ] 6.5 Formulario en la página / botón + modal según el mes visible: formulario en meses actuales o futuros sin presupuestos, botón cuando los hay, nada en meses pasados
- [ ] 6.6 Ritmo de gasto en la tarjeta del mes en curso ("a este ritmo acabarás en X")
- [ ] 6.7 Botón "Copiar del mes anterior" con selección y montos editables
- [ ] 6.8 Vista de recomendaciones con `basis` visible y acciones "Aplicar sugerido" / "Crear presupuesto"
- [ ] 6.9 `AppLayout`: `POST /notifications/check` una vez por carga autenticada y luego invalidar el contador; `features/notifications/` muestra el resumen de cierre y el aviso de categoría borrada
- [ ] 6.10 Tests de Vitest para 6.2–6.9

## 7. Verificación

- [ ] 7.1 Backend `ruff` / `mypy` / `pytest --cov` (≥70%); frontend `eslint` / `tsc` / `vitest --coverage` (≥70%)
- [ ] 7.2 Smoke test: crear presupuesto que se repite y comprobar que no aparece en el mes anterior; cambiar "solo este mes" y "este mes y los siguientes" con un mes planificado a mano; borrar con ambos alcances; intentar editar un mes pasado; cruzar 80% y 100% y ver un solo aviso de cada; importar un extracto que cruce el umbral; recargar la app y ver un aviso pendiente creado sin duplicar; simular cambio de mes y ver el resumen de cierre; copiar del mes anterior; borrar una categoría con historial; pedir y aplicar una recomendación
