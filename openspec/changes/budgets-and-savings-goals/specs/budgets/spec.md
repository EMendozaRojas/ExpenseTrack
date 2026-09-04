## Purpose

Topes de gasto mensuales por categoría para un usuario autenticado: cálculo de lo gastado en el mes contra un tope efectivo (con arrastre opcional del sobrante), estado (dentro / aviso / excedido) y alertas idempotentes al cruzar el 80% y el 100%, más recomendaciones de ajuste basadas en el gasto histórico.

## ADDED Requirements

### Requirement: User can set a monthly spending cap on any expense category
The system SHALL allow an authenticated user to create, update, deactivate and delete a monthly budget on any of their visible expense categories, whether a root or a subcategory, with an `amount`, a `currency` (default `EUR`), a `starts_on` month, and a `rollover` flag (default off). A user SHALL have at most one active budget per `(category, starts_on)`. Budgets SHALL be isolated per user.

#### Scenario: Create a budget on a root category
- **WHEN** the user sets a 300.00 EUR monthly cap on their "Alimentación" root category
- **THEN** the system stores the active budget owned by that user

#### Scenario: Create a budget on a subcategory
- **WHEN** the user sets a cap on their "Suscripciones" subcategory
- **THEN** the system stores it, independent of any budget on that subcategory's parent

#### Scenario: Duplicate active budget
- **WHEN** the user creates a second active budget for the same category and start month
- **THEN** the system rejects the request with a conflict error

#### Scenario: Budget on a non-expense or foreign category
- **WHEN** the user targets an income category, or a category not visible to them
- **THEN** the system rejects the request

### Requirement: Spent aggregates the category subtree
For a budget on a root category, `spent` SHALL sum the user's expense transactions in that root and its subcategories for the month; for a budget on a subcategory, `spent` SHALL sum only that subcategory. `spent` SHALL exclude transfers, soft-deleted transactions, and transactions in a currency other than the budget's currency. Budgets SHALL be evaluated independently of one another; the system SHALL NOT prevent or warn about a budget on a root coexisting with one on its child.

#### Scenario: Root budget includes subcategory spending
- **WHEN** the user has expenses in "Alimentación > Supermercado" and a budget on "Alimentación"
- **THEN** those expenses count towards the "Alimentación" budget's `spent`

#### Scenario: Excluded movements
- **WHEN** computing `spent` for a budget
- **THEN** transfers, soft-deleted transactions, and other-currency transactions in that category do not contribute

### Requirement: The effective cap carries over unspent budget when rollover is on
For each month from `starts_on`, the system SHALL compute `effective_amount = amount + carryover`, where `carryover` is `0` for the first month and, when `rollover` is on, `max(0, effective_amount(previous month) - spent(previous month))` thereafter; when `rollover` is off, `carryover` is always `0`. `effective_amount` SHALL never be below `amount` (overspending does not carry debt forward). `GET /budgets` for a month SHALL report `amount`, `carryover`, `effective_amount`, `spent`, `pct` and `status`.

#### Scenario: Unspent budget rolls forward
- **WHEN** a rollover budget of 300.00 has 250.00 spent in month 1
- **THEN** month 2's `effective_amount` is 350.00

#### Scenario: Overspending does not create debt
- **WHEN** a rollover budget of 300.00 has 340.00 spent in month 1
- **THEN** month 2's `effective_amount` is 300.00, not 260.00

#### Scenario: Rollover off
- **WHEN** a budget has `rollover` off
- **THEN** every month's `effective_amount` equals `amount` regardless of prior months

### Requirement: Budget status reflects spending against the effective cap
For a given month the system SHALL report `pct = spent / effective_amount` (may exceed 100) and a `status` of `ok` (`pct` below 80), `warning` (`pct` from 80 to under 100) or `exceeded` (`pct` 100 or more).

#### Scenario: Spending crosses into warning
- **WHEN** the user's `spent` in a budgeted category reaches 80% of the effective cap for the month
- **THEN** that budget's status for the month is `warning`

### Requirement: Threshold crossings raise idempotent alerts
When `spent` for a budgeted category in a month first reaches 80% or 100% of the `effective_amount`, the system SHALL record a budget alert for that `(budget, month, threshold)`. The same `(budget, month, threshold)` SHALL NOT produce more than one alert. Recalculation SHALL happen synchronously when transactions in the category change and when a statement import is committed, with a daily reconciliation job as a backstop.

#### Scenario: Alert recorded once
- **WHEN** spending crosses 100% of a cap and later more expenses are added in the same month
- **THEN** exactly one 100% alert exists for that budget and month

#### Scenario: Alert after a bulk import
- **WHEN** a committed import pushes a budgeted category past 80% for the month
- **THEN** an 80% alert for that budget and month is recorded as part of the import commit

#### Scenario: Reconciliation job fills a missed alert
- **WHEN** the daily job finds a budgeted category over a threshold for the current month with no corresponding alert
- **THEN** it records the missing alert and creates no duplicate for thresholds already alerted

### Requirement: System recommends budget adjustments from history
On request, for each expense category with enough recent history, the system SHALL return a recommended monthly cap and a flag of `raise`, `lower`, `keep`, or `create`, together with the basis of the recommendation. The recommendation SHALL use the three complete calendar months before the current one; a category SHALL be considered only if at least two of those months had spending, and the suggested amount SHALL be the rounded mean of the months that had spending. For a category with an active budget the flag SHALL be `keep` when the suggestion is within 10% of the current `amount`, otherwise `raise` or `lower`. For a category with no budget and spending in all three months, the flag SHALL be `create`.

#### Scenario: Adjust an existing budget
- **WHEN** the user requests recommendations and a budgeted category's recent mean spend is more than 10% above its cap
- **THEN** the response flags that budget `raise`, with the suggested amount and the three monthly spend values as basis

#### Scenario: Suggest a new budget
- **WHEN** an unbudgeted category had spending in each of the last three complete months
- **THEN** the response includes a `create` recommendation for it with the suggested amount

#### Scenario: Insufficient history
- **WHEN** a category had spending in only one of the last three months
- **THEN** no recommendation is returned for it
