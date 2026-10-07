## Purpose

Movimientos en una moneda distinta a la de su cuenta, convertidos con tipos de cambio por fecha cargados manualmente, conservando el importe y la moneda originales.

## ADDED Requirements

### Requirement: Exchange rates are stored per date
The system SHALL store exchange rates keyed by `(date, base, quote)`, loaded manually through the API and shared by all users. A rate SHALL be greater than zero, and at most one rate SHALL exist per date and currency pair. There is no automatic download of rates.

#### Scenario: Load a rate
- **WHEN** an authenticated user loads the USD→EUR rate for 7 October 2026
- **THEN** the rate is stored and listed, newest first

#### Scenario: Duplicate rate
- **WHEN** a rate already exists for that date and currency pair
- **THEN** the system rejects the new one with a conflict error

### Requirement: A movement in a foreign currency records the rate used
When a transaction is recorded in a currency different from its account's currency, the system SHALL convert the amount with the rate of the transaction's date (the direct rate, or the inverse of the opposite pair if only that one exists) and SHALL store the original amount and currency, the rate applied and the amount converted to the account currency. If no rate exists for that date, the system SHALL reject the transaction with a validation error. A transaction in the account's currency needs no rate.

#### Scenario: Foreign-currency expense
- **WHEN** the user records a USD expense on a EUR account and a USD→EUR rate exists for that date
- **THEN** the system stores the USD amount and currency, the rate used and the amount in EUR

#### Scenario: Inverse rate
- **WHEN** only the EUR→USD rate exists for that date
- **THEN** the system converts using its inverse

#### Scenario: Missing rate
- **WHEN** no rate exists for that date and currency pair
- **THEN** the system rejects the transaction with a validation error and stores nothing
