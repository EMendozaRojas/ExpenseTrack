## Purpose

Topes de gasto mensuales por categoría para un usuario autenticado: cálculo de lo gastado en el mes contra el tope, estado (dentro / aviso / excedido) y avisos al cruzar el 80% y el 100%.

## ADDED Requirements

### Requirement: User can set a monthly spending cap on any expense category
The system SHALL allow an authenticated user to create, update (`amount`, `is_active`) and delete a monthly budget on any of their visible expense categories, whether a root or a subcategory. A budget is recurring: the same budget SHALL be evaluated against whichever month is queried. A user SHALL have at most one budget per category. Budgets SHALL be isolated per user. `amount` SHALL be greater than zero.

#### Scenario: Create a budget on a root category
- **WHEN** the user sets a 300.00 monthly cap on their "Alimentación" root category
- **THEN** the system stores the active budget owned by that user

#### Scenario: Create a budget on a subcategory
- **WHEN** the user sets a cap on their "Suscripciones" subcategory
- **THEN** the system stores it, independent of any budget on that subcategory's parent

#### Scenario: Duplicate budget
- **WHEN** the user creates a second budget for a category that already has one
- **THEN** the system rejects the request with a conflict error

#### Scenario: Budget on a non-expense or foreign category
- **WHEN** the user targets an income category, or a category not visible to them
- **THEN** the system rejects the request with a "not found" error

#### Scenario: Non-positive amount
- **WHEN** the user sends an `amount` of zero or less
- **THEN** the system rejects the request with a validation error

### Requirement: Spent aggregates the category subtree
For a given month, for a budget on a root category, `spent` SHALL sum the user's expense transactions in that root and its subcategories; for a budget on a subcategory, `spent` SHALL sum only that subcategory. `spent` SHALL exclude non-expense transactions and soft-deleted transactions. Budgets SHALL be evaluated independently of one another; the system SHALL NOT prevent or warn about a budget on a root coexisting with one on its child.

#### Scenario: Root budget includes subcategory spending
- **WHEN** the user has expenses in "Alimentación > Supermercado" and a budget on "Alimentación"
- **THEN** those expenses count towards the "Alimentación" budget's `spent`

#### Scenario: Root and subcategory budgets are independent
- **WHEN** the user has budgets on both "Alimentación" and "Alimentación > Supermercado"
- **THEN** a supermarket expense counts towards both, each evaluated on its own

#### Scenario: Excluded movements
- **WHEN** computing `spent` for a budget
- **THEN** soft-deleted transactions and non-expense transactions in that category do not contribute

### Requirement: Budget status reflects spending against the cap
`GET /budgets?year=&month=` SHALL return each of the user's budgets with `amount`, `spent`, `pct = spent / amount × 100` (rounded to one decimal, may exceed 100) and a `status` of `ok` (`pct` below 80), `warning` (`pct` from 80 to under 100) or `exceeded` (`pct` 100 or more), computed for the requested month.

#### Scenario: Spending crosses into warning
- **WHEN** the user's `spent` in a budgeted category reaches 80% of the cap for the month
- **THEN** that budget's status for the month is `warning`

#### Scenario: Spending exceeds the cap
- **WHEN** the user's `spent` reaches 100% or more of the cap for the month
- **THEN** that budget's status for the month is `exceeded`

### Requirement: Threshold crossings raise notifications
After the user creates or updates a transaction, the system SHALL evaluate every active budget of that user for the current month and, when `pct` is 100 or more, SHALL create a `budget_exceeded` notification, or else when `pct` is 80 or more, a `budget_warning` notification. The same `(budget, type, month)` SHALL NOT produce more than one notification. When email delivery is configured, the system SHALL also send the notification by email; when it is not configured, the notification is still created.

#### Scenario: Warning notification once per month
- **WHEN** an expense pushes a budget past 80% and later another expense keeps it between 80% and 100% in the same month
- **THEN** exactly one `budget_warning` notification exists for that budget and month

#### Scenario: Exceeded notification
- **WHEN** an expense pushes a budget to 100% or more in the current month
- **THEN** a `budget_exceeded` notification is created for that budget and month
