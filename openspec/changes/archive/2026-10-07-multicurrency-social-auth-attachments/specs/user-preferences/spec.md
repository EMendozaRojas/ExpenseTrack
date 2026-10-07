## Purpose

Preferencias de un usuario autenticado: su moneda base, que es la de presupuestos, metas y totales, y su idioma y región.

## ADDED Requirements

### Requirement: Every user has preferences with sensible defaults
The system SHALL maintain a preferences record per user with `base_currency` (ISO 4217) and `locale`. If a user has none yet, the system SHALL create it with the defaults (`base_currency` `EUR`) the first time it is needed. The response SHALL also tell whether the user already has transactions.

#### Scenario: New user gets default preferences
- **WHEN** a newly registered user reads their preferences
- **THEN** the system returns `base_currency` `EUR`, the default locale and `has_transactions` false

### Requirement: User can update their preferences
The system SHALL allow the user to update their base currency and locale; fields not sent stay unchanged. The base currency SHALL be a three-letter ISO 4217 code (normalized to upper case) and SHALL only be changeable while the user has no transactions.

#### Scenario: Change base currency before recording movements
- **WHEN** a user without transactions sets `base_currency` to `usd`
- **THEN** the base currency becomes `USD`

#### Scenario: Base currency locked once there are transactions
- **WHEN** a user with transactions tries to change the base currency
- **THEN** the system rejects the request with a conflict error

#### Scenario: Invalid currency code
- **WHEN** the user sends a base currency that is not three letters
- **THEN** the system rejects the request with a validation error
