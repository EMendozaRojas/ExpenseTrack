## Purpose

Ajustes regionales de un usuario autenticado —moneda base, locale, zona horaria y formato— que condicionan cómo se agregan los importes y cómo se resuelven los rangos de fecha relativos ("hoy", "esta semana").

## ADDED Requirements

### Requirement: Every user has preferences with sensible defaults
The system SHALL maintain a preferences record per user containing `base_currency` (ISO 4217), `locale`, `timezone`, and week start. On registration the system SHALL create it with defaults (`base_currency` `EUR`), and existing users SHALL be backfilled with those defaults.

#### Scenario: New user gets default preferences
- **WHEN** a user registers
- **THEN** the system creates their preferences with `base_currency` `EUR` and a default locale and timezone

### Requirement: User can update their preferences
The system SHALL allow the user to update their own preferences. Changes SHALL take effect on subsequent requests that depend on them.

#### Scenario: Change base currency
- **WHEN** the user sets `base_currency` to `USD`
- **THEN** later stats requests that ask for conversion use `USD` as the target

#### Scenario: Timezone affects relative ranges
- **WHEN** the user sets their timezone and requests "this month" stats
- **THEN** the month boundaries are computed in that timezone
