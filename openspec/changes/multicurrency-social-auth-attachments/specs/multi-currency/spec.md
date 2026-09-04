## Purpose

Soporte de cuentas y movimientos en distintas monedas para un usuario autenticado, con tasas de cambio fechadas y conversión opcional a la moneda base en las agregaciones, sin alterar el importe original registrado.

## ADDED Requirements

### Requirement: Exchange rates are stored per date
The system SHALL maintain exchange rates keyed by `(date, base, quote)`, refreshed from an external daily source. When a rate for a requested date is unavailable (weekend, holiday, or gap), the system SHALL use the most recent earlier rate and mark the result as approximate.

#### Scenario: Rate lookup on a non-publication day
- **WHEN** a conversion needs the rate for a Sunday with no published rate
- **THEN** the system uses the most recent prior rate and flags the value as approximate

### Requirement: A movement in a foreign currency records the rate used
When a transaction is recorded in a currency different from its account's currency, the system SHALL store the original amount and currency, the exchange rate applied, and the amount converted to the account currency. The original amount and currency SHALL NOT change on later rate updates.

#### Scenario: Foreign-currency expense
- **WHEN** the user records a USD expense on a EUR account
- **THEN** the system stores the USD amount and currency, the EUR amount, and the rate used, and the account balance moves by the EUR amount

### Requirement: Stats can optionally convert to a target currency
The stats aggregations SHALL accept an optional target currency; when given, the system SHALL return, alongside the per-currency figures, a total converted using each movement's date rate. Without the parameter, aggregation stays per currency.

#### Scenario: Converted monthly total
- **WHEN** the user requests the monthly summary with conversion to their base currency
- **THEN** the system returns the per-currency totals plus a single converted total using each movement's date rate

#### Scenario: No conversion requested
- **WHEN** the user requests stats without a target currency
- **THEN** the system returns figures grouped by currency only
