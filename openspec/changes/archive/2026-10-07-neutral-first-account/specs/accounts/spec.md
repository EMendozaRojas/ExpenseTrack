## MODIFIED Requirements

### Requirement: User can create and manage accounts
The system SHALL allow an authenticated user to create, list, update and archive their own accounts. Each account SHALL have a name, a type (`general`, `checking`, `savings`, `credit_card`, `cash`, `wallet`), a currency (ISO 4217, default `EUR`) and an initial balance (default `0`). The type SHALL be optional when creating an account and SHALL default to `general` ("not specified"). Accounts SHALL be isolated per user: a user SHALL never see or modify another user's account.

#### Scenario: Create account
- **WHEN** the user submits a name, type and currency
- **THEN** the system creates the account owned by that user with initial balance `0` unless another value is provided

#### Scenario: Create account without a type
- **WHEN** the user creates their first account giving only its name
- **THEN** the system creates it with type `general`

#### Scenario: List only own accounts
- **WHEN** the user requests the account list
- **THEN** the system returns only accounts owned by that user, ordered by name, including each account's current balance

#### Scenario: Update keeps the initial balance
- **WHEN** the user updates an account's name, type or currency
- **THEN** the system applies only the fields sent and the initial balance does not change

#### Scenario: Accessing another user's account
- **WHEN** the user requests or updates an account owned by a different user
- **THEN** the system responds with a "not found" error without revealing that the account exists
