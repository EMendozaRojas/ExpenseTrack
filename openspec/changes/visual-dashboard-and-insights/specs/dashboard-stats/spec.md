## Purpose

Agregaciones de solo lectura sobre los movimientos de un usuario autenticado que alimentan el dashboard: resumen de ingresos, gastos, neto y saldo; distribución del gasto por categoría; comparativa de ingresos frente a gastos por periodo; y evolución del saldo en el tiempo, todo filtrable por rango de fechas y granularidad y calculado en la base de datos.

## ADDED Requirements

### Requirement: Stats endpoints operate only on the requesting user's data
Every stats result SHALL be computed only from the requesting user's non-deleted transactions, and SHALL accept a `date_from` and `date_to` range. Transfer transactions SHALL be excluded from income and expense figures.

#### Scenario: Isolation
- **WHEN** a user requests any stats endpoint
- **THEN** the figures reflect only that user's transactions

#### Scenario: Transfers excluded
- **WHEN** the user has transfers between their accounts within the range
- **THEN** those transfers do not count towards income or expense totals

### Requirement: Summary of income, expense, net and balance
The system SHALL return, for a range, the total income, total expense, net (income minus expense) and the account balance, broken down by currency, optionally scoped to one account. It SHALL also return a `savings_rate` (`net / income` for the range) and a `tier` classifying it, both computed server-side.

#### Scenario: Monthly summary
- **WHEN** the user requests the summary for a calendar month
- **THEN** the system returns income, expense, net and balance for that month per currency, plus `savings_rate` and its `tier`

#### Scenario: No income in the range
- **WHEN** the range has expense but no income
- **THEN** the system returns `savings_rate` as undefined/null rather than dividing by zero, with a `tier` indicating no data

### Requirement: Expense distribution by category
The system SHALL return, for a range, the total expense per category with each category's share of the range's total expense, suitable for a donut chart.

#### Scenario: Category breakdown
- **WHEN** the user requests the by-category breakdown for a range
- **THEN** each entry has a category, a total, and a percentage, and the percentages sum to 100 (within rounding)

### Requirement: Income vs expense series by period
The system SHALL return a time series of income and expense totals bucketed by a requested granularity (`day`, `week`, `month`, `year`) over the range, with empty buckets represented as zero.

#### Scenario: Monthly bars for a year
- **WHEN** the user requests income-vs-expense with `month` granularity over a year
- **THEN** the system returns 12 buckets, each with an income and an expense total, zero where there is no activity

### Requirement: Balance trend over time
The system SHALL return the running account balance at each point of a requested granularity over the range, optionally for a single account, starting from the balance as of the range start.

#### Scenario: Daily balance line
- **WHEN** the user requests the balance trend with `day` granularity for a month on one account
- **THEN** the system returns one balance point per day, each reflecting all of that account's activity up to and including that day

### Requirement: Top expenses by impact
The system SHALL return, for a range, the top N expense categories (and optionally individual transactions) ranked by total amount.

#### Scenario: Top 5 categories
- **WHEN** the user requests top expenses with N=5 for a range
- **THEN** the system returns the 5 categories with the highest expense totals in that range, largest first
