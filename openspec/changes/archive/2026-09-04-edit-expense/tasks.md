## 1. Backend

- [ ] 1.1 Add an `ExpenseUpdate` Pydantic schema in `app/schemas/expense.py` (amount, description, expense_date, category_id)
- [ ] 1.2 Add a `PUT /expenses/{expense_id}` handler in `app/routers/expenses.py` that reuses the same ownership check as `delete_expense` and the same category-visibility check as `create_expense`
- [ ] 1.3 Add pytest coverage: successful edit, invalid amount, category not accessible, editing another user's expense (404), editing a nonexistent expense (404)

## 2. Frontend - API layer

- [ ] 2.1 Add an `updateExpense` function in `features/expenses/api.ts`
- [ ] 2.2 Add a test for `updateExpense` in `features/expenses/api.test.ts`

## 3. Frontend - ExpenseForm edit mode

- [ ] 3.1 Extend `ExpenseForm` to accept an optional `expense` prop: when present, pre-fill the fields and submit via update instead of create
- [ ] 3.2 Update `ExpenseForm.test.tsx` to cover the edit mode (pre-filled values, submit calls update)

## 4. Frontend - ExpenseList and page wiring

- [ ] 4.1 Add an "Editar" button per row in `ExpenseList`
- [ ] 4.2 Add editing state in `MonthlyExpensesPage` (selected expense), render `ExpenseForm` in edit mode when set, wire the update mutation with cache invalidation for `expenses` and `summary`
- [ ] 4.3 Update `MonthlyExpensesPage.test.tsx` to cover clicking "Editar" and submitting the update

## 5. Verification

- [ ] 5.1 Run backend `ruff` / `mypy` / `pytest --cov` and frontend `eslint` / `tsc` / `vitest --coverage`; keep coverage at or above 70%
- [ ] 5.2 Smoke test the new endpoint end-to-end against the running stack
