<!-- Implementar después de `monthly-budgets-planning`. -->

## 1. Backend

- [ ] 1.1 `GET /goals/suggestions` según D1 (fondo de emergencia con cobertura y tramo, independencia financiera, "sin datos suficientes"); tests

## 2. Frontend

- [ ] 2.1 `features/goals/`: selector "Empezar desde una sugerencia" en el formulario de crear meta, que rellena nombre e importe editables; muestra el `basis`, la cobertura y el tramo del fondo de emergencia
- [ ] 2.2 `features/dashboard/`: tarjeta de presupuestos en aviso/excedidos del mes seleccionado y tarjeta de metas activas, compartiendo query keys con las páginas
- [ ] 2.3 Tests de Vitest para 2.1–2.2

## 3. Verificación

- [ ] 3.1 Backend `ruff` / `mypy` / `pytest --cov` (≥70%); frontend `eslint` / `tsc` / `vitest --coverage` (≥70%)
- [ ] 3.2 Smoke test: crear una meta desde el preset de fondo de emergencia editando el importe; ver en el dashboard un presupuesto excedido y las metas activas; cambiar el mes del dashboard y ver la tarjeta de presupuestos actualizada
