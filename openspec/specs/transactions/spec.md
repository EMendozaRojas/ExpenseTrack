# transactions Specification

## Purpose
Registra y consulta los movimientos financieros de un usuario (ingreso, gasto, transferencia) asociados a una de sus cuentas, con importe firmado, categoría opcional, pertenencia por usuario y borrado lógico que preserva la identidad y el histórico del apunte.

## Requirements

### Requirement: User can record a transaction on one of their accounts
The system SHALL allow an authenticated user to record a transaction on an account they own, with a signed `amount`, a `posted_at` date, a `direction` (`income`, `expense`, `transfer`), an optional `category_id`, an optional free-text `description`/`note`, and an optional `counterparty`. A negative amount SHALL represent money leaving the account and a positive amount money entering it; `direction` SHALL be consistent with the sign for `income`/`expense`.

#### Scenario: Record a cash expense
- **WHEN** the user submits an expense with amount, date and category on an account they own
- **THEN** the system stores the transaction with a negative amount, `direction='expense'`, `source='manual'` and returns it

#### Scenario: Amount must be non-zero and consistent with direction
- **WHEN** the user submits a transaction whose amount is zero, or whose sign contradicts its `direction` (a positive amount for `expense`, or a negative amount for `income`)
- **THEN** the system rejects the request with a validation error and stores nothing

#### Scenario: Category must be accessible to the user
- **WHEN** the user submits a `category_id` that does not exist or belongs to a different user
- **THEN** the system rejects the request with a "not found" error and stores nothing

#### Scenario: Account must belong to the user
- **WHEN** the user submits a transaction against an account owned by a different user
- **THEN** the system responds with a "not found" error and stores nothing

### Requirement: User can list and filter their transactions
The system SHALL return only the requesting user's transactions, filterable by account, category, direction, date range and free-text query, ordered by `posted_at` descending, paginated with a cursor (not offset). Soft-deleted transactions SHALL be excluded by default.

#### Scenario: Filter by month and account
- **WHEN** the user requests transactions for a given account and date range
- **THEN** the system returns only that user's non-deleted transactions matching both filters, newest first

#### Scenario: Pagination via cursor
- **WHEN** the user requests the next page using the cursor returned by a previous call
- **THEN** the system returns the following transactions without repeating or skipping any

### Requirement: User can edit and soft-delete their transactions
The system SHALL allow the owner to update `amount`, `posted_at`, `category_id`, `direction`, `counterparty` and `note` of their transaction (all of them are sent on each edit; an omitted category means "Sin Clasificar"), and to soft-delete it. The `id`, `owner_id`, `account_id`, currency and `created_at` SHALL NOT change on edit. Edits SHALL enforce the same amount and category rules as recording a transaction. Transfers SHALL NOT be editable. A soft-deleted transaction SHALL stop affecting balances and reports but SHALL remain recoverable from the trash.

#### Scenario: Edit keeps identity
- **WHEN** the owner submits new values for an existing transaction
- **THEN** the system updates it in place and its `id` and `created_at` are unchanged

#### Scenario: Edit rejects an invalid amount
- **WHEN** the owner edits a transaction to a zero amount or a sign inconsistent with its direction
- **THEN** the system rejects the update with a validation error and leaves the transaction unchanged

#### Scenario: Edit rejects an inaccessible category
- **WHEN** the owner edits a transaction to a `category_id` that does not exist or belongs to another user
- **THEN** the system rejects the update with a "not found" error and leaves the transaction unchanged

#### Scenario: Transfers cannot be edited
- **WHEN** the owner edits a leg of a transfer
- **THEN** the system rejects the request with a conflict error

#### Scenario: Editing or deleting another user's transaction
- **WHEN** a user edits or deletes a transaction owned by a different user
- **THEN** the system responds with a "not found" error and changes nothing

### Requirement: Deleted transactions stay in a 30-day trash
Soft-deleted transactions SHALL be listed in a trash with the date they were deleted and the date they will be permanently removed, 30 days after deletion. The owner SHALL be able to restore a transaction from the trash (both legs, for a transfer). Transactions older than 30 days in the trash SHALL be permanently removed the next time the trash is accessed or a transaction is deleted or restored.

#### Scenario: Restore from the trash
- **WHEN** the owner restores a transaction deleted 3 days ago
- **THEN** it is no longer in the trash and counts again in balances and reports

#### Scenario: Expired transactions are purged
- **WHEN** the owner opens the trash and a transaction was deleted 31 days ago
- **THEN** that transaction has been permanently removed and is not listed

### Requirement: Transfers between own accounts are linked
The system SHALL allow the user to move money between two accounts they own in a single operation that creates two linked transactions — a negative one on the source account and a positive one on the destination account — sharing a `transfer_group_id` and `direction='transfer'`, with no category. Transfers SHALL be excluded from income and expense totals in statistics.

#### Scenario: Create a transfer
- **WHEN** the user transfers 50.00 from account A to account B, both owned by them
- **THEN** the system creates a -50.00 transaction on A and a +50.00 transaction on B with the same `transfer_group_id`

#### Scenario: Transfer requires both accounts owned by the user
- **WHEN** the user attempts a transfer where the source or destination account is not theirs
- **THEN** the system responds with a "not found" error and creates nothing

#### Scenario: Deleting one leg deletes the whole transfer
- **WHEN** the user soft-deletes either leg of a transfer
- **THEN** the system soft-deletes both legs sharing that `transfer_group_id`, and both accounts' balances are restored accordingly
