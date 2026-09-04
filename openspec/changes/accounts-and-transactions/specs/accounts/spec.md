## Purpose

Gestiona las cuentas financieras de un usuario autenticado (banco, efectivo, tarjeta, ahorro) y expone su saldo como el saldo inicial más la suma de sus movimientos no borrados.

## ADDED Requirements

### Requirement: User can create and manage accounts
The system SHALL allow an authenticated user to create, list, update and archive their own accounts. Each account SHALL have a name, a type (`checking`, `savings`, `credit_card`, `cash`, `wallet`), a currency (ISO 4217, default `EUR`) and an initial balance (default `0`). Accounts SHALL be isolated per user: a user SHALL never see or modify another user's account.

#### Scenario: Create account
- **WHEN** the user submits a name, type and currency
- **THEN** the system creates the account owned by that user with initial balance `0` unless another value is provided

#### Scenario: List only own accounts
- **WHEN** the user requests the account list
- **THEN** the system returns only accounts owned by that user, ordered by name, including each account's current balance

#### Scenario: Accessing another user's account
- **WHEN** the user requests or updates an account owned by a different user
- **THEN** the system responds with a "not found" error without revealing that the account exists

### Requirement: Account balance is derived from its movements
The system SHALL compute an account's balance as `initial_balance` plus the sum of the signed amounts of its non-deleted transactions. The balance SHALL update automatically when transactions are added, edited, or soft-deleted.

#### Scenario: Balance after adding an expense
- **WHEN** the user adds an expense of 20.00 to an account whose balance is 100.00
- **THEN** the account's reported balance becomes 80.00

#### Scenario: Deleted transactions do not count
- **WHEN** a transaction on the account is soft-deleted
- **THEN** the account's balance is recomputed as if that transaction did not exist

### Requirement: Archived accounts are retained, not deleted
The system SHALL NOT allow hard deletion of an account that has transactions; instead the user SHALL be able to archive it. Archived accounts SHALL be excluded from default listings and from selection when creating a new transaction, but their historical transactions SHALL remain intact and visible in reports.

#### Scenario: Archive an account with movements
- **WHEN** the user archives an account that has transactions
- **THEN** the account is marked archived, its transactions are preserved, and it no longer appears in the default account list
