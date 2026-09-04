## Purpose

Diagnóstico automático del gasto de un usuario autenticado: identificación de las categorías de mayor impacto, detección de pagos recurrentes que el usuario confirma o descarta, y detección de gasto hormiga (acumulación de muchos movimientos pequeños).

## ADDED Requirements

### Requirement: System surfaces the highest-impact expense categories
The system SHALL identify, for a range, the expense categories with the largest total and their share of total expense, so the user can see where the money goes. For root categories, the system SHALL additionally flag whether that share exceeds its reference band, so the user can spot categories running above what is typical.

#### Scenario: Impact ranking
- **WHEN** the user opens the diagnosis for a range
- **THEN** the system lists their expense categories ordered by total, each with its amount and percentage of the range's expense

#### Scenario: Above-typical spending flagged
- **WHEN** a root category's share of the range's expense exceeds its reference band
- **THEN** that category is flagged as above typical in the response

#### Scenario: Subcategories are not flagged
- **WHEN** the ranked list includes a subcategory
- **THEN** it has no above-typical flag, regardless of its share

### Requirement: System detects recurring payments as suggestions
The system SHALL detect likely recurring payments by grouping the user's transactions by normalized counterparty and finding groups with at least the configured number of occurrences at a consistent cadence and a stable amount. Detected series SHALL be presented as unconfirmed suggestions; the user SHALL be able to confirm or dismiss each. The system SHALL NOT take any automatic action based on an unconfirmed series.

#### Scenario: Recurring subscription detected
- **WHEN** the user has monthly charges from the same counterparty of a similar amount over several months
- **THEN** the system presents an unconfirmed recurring series for that counterparty with its cadence and typical amount

#### Scenario: User dismisses a suggestion
- **WHEN** the user dismisses a detected recurring series
- **THEN** it is no longer presented as a suggestion

#### Scenario: One-off purchases are not recurring
- **WHEN** a counterparty appears only once or twice, or with irregular timing
- **THEN** no recurring series is suggested for it

#### Scenario: Recurring income is detected too
- **WHEN** the user receives a similarly-sized payment from the same counterparty on a consistent monthly cadence (e.g. a salary)
- **THEN** the system presents it as an unconfirmed recurring series the same way it would an expense

### Requirement: User can configure ant-expense detection thresholds
The system SHALL let each user configure their own per-transaction amount threshold, minimum group count, and minimum group aggregate for ant-expense detection, defaulting to 10.00 (in their currency), 5, and 30.00 respectively when the user has not set any. Reading the settings SHALL NOT require the user to have saved any; saving SHALL create or update them.

#### Scenario: Defaults before any configuration
- **WHEN** a user who never configured ant-expense settings requests them
- **THEN** the system returns the default threshold (10.00), minimum count (5), and minimum aggregate (30.00)

#### Scenario: User saves custom thresholds
- **WHEN** the user sets a per-transaction threshold of 20.00 and a minimum count of 3
- **THEN** subsequent ant-expense detection for that user uses those values instead of the defaults

### Requirement: System detects "ant expense"
The system SHALL identify, for a range, accumulations of many small expense transactions — each at or below the user's configured per-transaction threshold — grouped by normalized counterparty, and report the groups whose count reaches the user's configured minimum count and whose aggregate reaches the user's configured minimum aggregate. This detection SHALL NOT persist a series.

#### Scenario: Small purchases add up
- **WHEN** the user has, within the range, at least their configured minimum count of sub-threshold expenses at the same counterparty summing to at least their configured minimum aggregate
- **THEN** the system reports that counterparty with the count and aggregate total of those small expenses

#### Scenario: Below significance
- **WHEN** small expenses at a counterparty fall short of the configured minimum count or minimum aggregate
- **THEN** that counterparty is not reported as ant expense
