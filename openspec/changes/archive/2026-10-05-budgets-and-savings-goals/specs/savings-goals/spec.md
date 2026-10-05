## Purpose

Metas de ahorro de un usuario autenticado: un objetivo con importe y fecha opcional, el registro de aportaciones que hacen avanzar el progreso, avisos al acercarse y al alcanzar el objetivo, y una proyección de cuándo se alcanzará al ritmo actual.

## ADDED Requirements

### Requirement: User can define a savings goal
The system SHALL allow an authenticated user to create, update and delete a savings goal with a `name`, a `target_amount` greater than zero, an optional `target_date`, an optional linked account owned by the user, and a `status` of `active`, `completed` or `archived` (default `active`). Goals SHALL be isolated per user. The linked account SHALL be informational only: the system SHALL NOT derive `current_amount` from that account's balance.

#### Scenario: Create a goal
- **WHEN** the user creates a "Fondo de emergencia" goal with target 6000.00 and a target date
- **THEN** the system stores it as active with current amount 0, owned by that user

#### Scenario: Linked account must belong to the user
- **WHEN** the user links a goal to an account they do not own
- **THEN** the system rejects the request with a "not found" error

#### Scenario: Accessing another user's goal
- **WHEN** the user requests or updates a goal owned by a different user
- **THEN** the system responds with a "not found" error

### Requirement: Contributions advance the goal
The system SHALL let the user add, list and delete contributions to a goal, each with an `amount` greater than zero, a date and an optional note. The goal's `current_amount` SHALL equal the sum of its contributions, and the goal SHALL report `pct = current_amount / target_amount × 100`. When a contribution brings an `active` goal's `current_amount` to or above `target_amount`, the goal's status SHALL become `completed`.

#### Scenario: Record a contribution
- **WHEN** the user adds a 200.00 contribution to a goal whose current amount is 500.00
- **THEN** the goal's current amount becomes 700.00

#### Scenario: Goal completed
- **WHEN** a contribution brings current amount to or above the target
- **THEN** the goal's status becomes `completed`

#### Scenario: Delete a contribution
- **WHEN** the user deletes one of a goal's contributions
- **THEN** it no longer counts towards the goal's current amount

### Requirement: Goal progress raises notifications
When a contribution is added, the system SHALL create a `goal_reached` notification if `current_amount` is at or above the target, or else a `goal_near` notification if it is at or above 80% of the target. Each `(goal, type)` SHALL produce at most one notification.

#### Scenario: Near the goal
- **WHEN** a contribution brings a goal to 80% of its target for the first time
- **THEN** a single `goal_near` notification is created for that goal

### Requirement: System projects the completion date
The system SHALL compute `monthly_pace` as the sum of contributions in the last three complete calendar months before the current one, counting only months starting on or after the goal's creation month, divided by the number of those months. The estimated completion date SHALL be today plus `ceil((target_amount - current_amount) / monthly_pace)` months. When no complete month has elapsed since creation or `monthly_pace` is zero, the system SHALL indicate there is not enough data instead of returning a date. When the goal is already at or above its target, the system SHALL return zero months remaining.

#### Scenario: Projection with a steady pace
- **WHEN** the user requests the projection for a goal with contributions in the last three complete months
- **THEN** the system returns the monthly pace, the months remaining and an estimated completion date

#### Scenario: Not enough data
- **WHEN** the goal was created this month, or had no contributions in the window
- **THEN** the system indicates there is not enough data to estimate rather than returning a date

#### Scenario: Goal already reached
- **WHEN** the goal's current amount is already at or above its target
- **THEN** the projection reports zero months remaining
