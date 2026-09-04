## Why

Right now a gasto mal registrado (monto, categoría, fecha o descripción incorrectos) solo se puede corregir borrándolo y creando uno nuevo. Eso pierde el registro original y es una fricción innecesaria para un caso de uso tan común como corregir un error de tipeo.

## What Changes

- Agregar un endpoint `PUT /api/v1/expenses/{expense_id}` en el backend que permite actualizar `amount`, `description`, `expense_date` y `category_id` de un gasto existente, solo si pertenece al usuario autenticado.
- Agregar una acción "Editar" en `ExpenseList` que abre `ExpenseForm` precargado con los valores actuales del gasto.
- `ExpenseForm` gana un modo de edición (además del modo creación actual), reutilizando la misma validación y el mismo flujo de selección/creación de categoría.

## Capabilities

### New Capabilities
- `expenses`: gestión de gastos — cubre la capacidad de editar un gasto existente (monto, descripción, fecha, categoría), con las mismas reglas de validación y pertenencia que ya aplican a crear/eliminar gastos.

### Modified Capabilities

(ninguna — `expenses` no tenía spec previo en este repo)

## Impact

- Backend: `app/routers/expenses.py` (nuevo handler `PUT`), `app/schemas/expense.py` (nuevo schema de entrada para actualización), `tests/` (tests del nuevo endpoint).
- Frontend: `features/expenses/api.ts` (nueva función `updateExpense`), `features/expenses/components/ExpenseForm.tsx` (modo edición), `features/expenses/components/ExpenseList.tsx` (botón "Editar"), `features/expenses/MonthlyExpensesPage.tsx` (wiring del estado de edición), tests correspondientes.
