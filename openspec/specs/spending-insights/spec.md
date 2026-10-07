# spending-insights Specification

## Purpose
Diagnóstico automático del gasto de un usuario autenticado: detección de pagos e ingresos recurrentes que el usuario puede descartar, y detección de gasto hormiga (muchos gastos pequeños en una misma subcategoría) con umbrales configurables.

## Requirements

### Requirement: System detects recurring payments as suggestions
The system SHALL detect, on demand over roughly the last 6 months, series of income or expense transactions grouped by normalized counterparty (or description) and direction, with at least 3 occurrences, amounts within ±25% of the group's mean and a regular cadence. Each series SHALL report its occurrences, average amount, cadence (`semanal`, `quincenal`, `mensual`, `trimestral` or `irregular`) and dates. Series are not stored. The user SHALL be able to dismiss a series and restore it; dismissed series are still returned, flagged as dismissed.

#### Scenario: Recurring subscription detected
- **WHEN** the user paid "NETFLIX" a similar amount each month for 4 months
- **THEN** a `mensual` expense series is returned for it

#### Scenario: User dismisses a suggestion
- **WHEN** the user dismisses a series
- **THEN** it is returned with `dismissed` true until the user restores it

#### Scenario: One-off purchases are not recurring
- **WHEN** a counterparty appears only twice
- **THEN** no series is returned for it

#### Scenario: Recurring income is detected too
- **WHEN** the user receives a payroll from the same payer every month
- **THEN** an income series is returned for it

### Requirement: User can configure ant-expense detection thresholds
The system SHALL let the user read and update three thresholds: the maximum amount of an expense to count as an ant expense (default 10.00), the minimum number of such expenses in the month (default 5) and the minimum aggregate in the month (default 30.00). Amounts SHALL be greater than zero and the count at least 1; fields not sent stay unchanged.

#### Scenario: Defaults before any configuration
- **WHEN** a user who never configured the thresholds reads them
- **THEN** the system returns 10.00, 5 and 30.00

#### Scenario: User saves custom thresholds
- **WHEN** the user sets the maximum amount to 5.00
- **THEN** later ant-expense detections use 5.00

### Requirement: System detects "ant expense"
For a given month, the system SHALL group the user's expenses at or below the maximum amount by subcategory and return the groups that reach both the minimum count and the minimum aggregate, with their count, aggregate and average, from highest to lowest aggregate.

#### Scenario: Small purchases add up
- **WHEN** the user made 10 coffee purchases of 3.50 in "Cafeterías" in the month, with the default thresholds
- **THEN** "Cafeterías" is returned with 10 occurrences, an aggregate of 35.00 and an average of 3.50

#### Scenario: Below significance
- **WHEN** a subcategory has 3 small expenses and the minimum count is 5
- **THEN** it is not returned
