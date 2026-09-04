## Purpose

Covers how an authenticated user manages the expenses they have logged, including correcting a previously registered expense without losing its identity or creation history.

## ADDED Requirements

### Requirement: User can edit an existing expense
The system SHALL allow an authenticated user to update the `amount`, `description`, `expense_date`, and `category_id` of an expense they own. The `id`, `owner_id`, and `created_at` of the expense SHALL NOT change as a result of an edit.

#### Scenario: Successful edit
- **WHEN** the owner submits new values for amount, description, date, and category on one of their existing expenses
- **THEN** the system updates the expense with the new values and returns the updated expense

#### Scenario: Amount must remain valid
- **WHEN** the owner submits an amount that is zero or negative
- **THEN** the system rejects the update with a validation error and leaves the expense unchanged

#### Scenario: Category must be accessible to the user
- **WHEN** the owner submits a `category_id` that does not exist or belongs to a different user
- **THEN** the system rejects the update with a "not found" error and leaves the expense unchanged

#### Scenario: Cannot edit another user's expense
- **WHEN** a user submits an update for an expense owned by a different user
- **THEN** the system rejects the request with a "not found" error, without revealing that the expense exists

#### Scenario: Editing a nonexistent expense
- **WHEN** the owner submits an update for an expense id that does not exist
- **THEN** the system rejects the request with a "not found" error
