# dashboard-stats Specification

## Purpose
Resumen mensual de solo lectura sobre los movimientos de un usuario autenticado que alimenta el dashboard: ingresos, gastos y neto, gastos fijos y variables, y gasto por categoría en árbol, opcionalmente filtrado por cuenta.

## Requirements

### Requirement: Monthly summary only uses the requesting user's data
`GET /dashboard/summary?year=&month=` SHALL aggregate only the requesting user's non-deleted transactions dated in that month, optionally restricted to one of their accounts. Transfers SHALL NOT count as income or expense. Filtering by an account the user does not own SHALL respond with a "not found" error.

#### Scenario: Transfers excluded
- **WHEN** the user has a transfer between two of their accounts in the month
- **THEN** it does not count in income, expense or net

#### Scenario: Filter by another user's account
- **WHEN** the user filters by an account they do not own
- **THEN** the system responds with a "not found" error

### Requirement: Summary of income, expense and net
The summary SHALL return the month's total income, total expense (positive), net (income minus expense) with a status `a_favor` when net is zero or positive and `en_contra` when negative, and the split of expense into fixed (subcategories marked as fixed) and variable.

#### Scenario: Monthly summary
- **WHEN** the user had 2000.00 income and 1500.00 expense in the month, 600.00 of it in fixed subcategories
- **THEN** net is 500.00 `a_favor`, fixed is 600.00 and variable is 900.00

### Requirement: Expense distribution by category
The summary SHALL break the expense down by root category, each with its subcategories, both ordered from highest to lowest spending.

#### Scenario: Category breakdown
- **WHEN** the user spent in "Alimentación > Supermercado" and "Alimentación > Restaurantes"
- **THEN** "Alimentación" appears with the sum of both and each subcategory with its own total

### Requirement: Incomplete data warning for the current month
For the current month, the summary SHALL flag `incomplete_data` when the latest income or expense of the month is more than 3 days old (or there is none), and SHALL return the date of the latest one.

#### Scenario: Stale current month
- **WHEN** the latest transaction of the current month is 5 days old
- **THEN** `incomplete_data` is true
