## Purpose

Metas de ahorro de un usuario autenticado: un objetivo con importe y fecha opcional, el registro de aportaciones que hacen avanzar el progreso, y una proyección de cuándo se alcanzará al ritmo actual.

## ADDED Requirements

### Requirement: User can define a savings goal
The system SHALL allow an authenticated user to create, update, and archive a savings goal with a `name`, a `target_amount`, an optional `target_date`, an optional linked account, and a `status` of `active`, `reached` or `archived`. Goals SHALL be isolated per user. A goal's `current_amount` SHALL start at zero. The linked account SHALL be informational only: the system SHALL NOT derive `current_amount` from that account's balance.

#### Scenario: Create a goal
- **WHEN** the user creates a "Fondo de emergencia" goal with target 6000.00 and a target date
- **THEN** the system stores it as active with current amount 0, owned by that user

#### Scenario: Accessing another user's goal
- **WHEN** the user requests or updates a goal owned by a different user
- **THEN** the system responds with a "not found" error

### Requirement: Contributions advance the goal
The system SHALL let the user record contributions to a goal, each with an `amount` and a date, optionally linked to a transaction. The goal's `current_amount` SHALL equal the sum of its contributions. When `current_amount` reaches `target_amount` the goal's status SHALL become `reached`.

#### Scenario: Record a contribution
- **WHEN** the user adds a 200.00 contribution to a goal whose current amount is 500.00
- **THEN** the goal's current amount becomes 700.00

#### Scenario: Goal reached
- **WHEN** a contribution brings current amount to or above the target
- **THEN** the goal's status becomes `reached`

### Requirement: System projects the completion date
The system SHALL estimate a goal's completion date as `start of current month + ceil((target_amount - current_amount) / monthly_rate)` months, where `monthly_rate` is the mean of contributions per month over the last three calendar months that had a contribution. When `monthly_rate` is zero or fewer than two of those months had a contribution, the system SHALL indicate the rate is insufficient instead of returning a date.

#### Scenario: Projection with a steady rate
- **WHEN** the user requests the projection for a goal with contributions in each of the last three months
- **THEN** the system returns an estimated completion date based on the mean monthly contribution and the remaining amount

#### Scenario: Not enough data
- **WHEN** the goal has contributions in fewer than two of the last three months
- **THEN** the system indicates the rate is insufficient to estimate rather than returning a date
