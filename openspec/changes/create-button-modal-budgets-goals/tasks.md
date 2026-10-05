<!-- Change documentado a posteriori: todas las tareas se implementaron en el commit 8fa949b (2026-10-05). -->

## 1. Presupuestos

- [x] 1.1 `BudgetsPage.tsx`: extraer el formulario a `budgetForm` y envolver selector de mes + acciones en `.expenses-toolbar`
- [x] 1.2 Mostrar el formulario en la página solo si la lista de presupuestos está vacía (y no está cargando)
- [x] 1.3 Botón "+ Nuevo presupuesto" en `.expenses-toolbar-actions` cuando hay presupuestos, que abre `Modal` titulado "Nuevo presupuesto"
- [x] 1.4 Cerrar el modal en `onSuccess` de la creación; mantenerlo abierto con el error en `onError`

## 2. Metas

- [x] 2.1 `GoalsPage.tsx`: extraer el formulario a `goalForm`
- [x] 2.2 Mostrar el formulario en la página solo si no hay metas (y no está cargando)
- [x] 2.3 Botón "+ Nueva meta" arriba a la derecha cuando hay metas, que abre `Modal` titulado "Nueva meta de ahorro"
- [x] 2.4 Cerrar el modal en `onSuccess` de la creación

## 3. Estilos

- [x] 3.1 Clase `.expenses-toolbar-end` (`justify-content: flex-end`) en `index.css` para alinear el botón a la derecha en Metas

## 4. Tests

- [x] 4.1 `BudgetsPage.test.tsx`: con presupuestos, el formulario está oculto y el botón abre el modal con el formulario
- [x] 4.2 `BudgetsPage.test.tsx`: sin presupuestos, se crea desde el formulario en la página
- [x] 4.3 `GoalsPage.test.tsx`: sin metas, se muestra el formulario y no el botón
- [x] 4.4 `GoalsPage.test.tsx`: con metas, se crea desde el botón + modal
- [x] 4.5 Tests de budgets y goals en verde y `tsc` sin errores
