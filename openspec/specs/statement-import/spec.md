# statement-import Specification

## Purpose
Permite a un usuario autenticado cargar un extracto bancario en CSV asociado a una de sus cuentas, ver una vista previa que clasifica cada fila frente a lo que ya tiene registrado, y confirmar la importación con una estrategia que nunca toca sus movimientos manuales.

## Requirements

### Requirement: User uploads a CSV statement against one of their accounts
The system SHALL accept a CSV file upload associated with an account the user owns, parse it synchronously and return a preview without creating any transaction. Files that are not CSV SHALL be rejected as an unsupported media type; files larger than 5 MB or with more than 10,000 rows SHALL be rejected as too large; files whose columns or values cannot be parsed SHALL be rejected with a validation error.

#### Scenario: Upload returns a preview
- **WHEN** the user uploads a CSV against their account
- **THEN** the system returns an import in `previewed` status with its rows, the date range of the file and the count of new, exact-duplicate and probable-duplicate rows, and no transaction is created yet

#### Scenario: Upload against another user's account
- **WHEN** the user uploads a file against an account they do not own
- **THEN** the system responds with a "not found" error

#### Scenario: Not a CSV
- **WHEN** the user uploads a `.pdf` or `.xlsx` file
- **THEN** the system rejects it as an unsupported media type

#### Scenario: Oversized file
- **WHEN** the user uploads a file larger than 5 MB or with more than 10,000 rows
- **THEN** the system rejects it as too large

### Requirement: Columns and values are recognized automatically
The system SHALL recognize the columns by their header names, case-insensitively: a date column (such as `Fecha`, `Date`, `Fecha valor`), a description column (such as `Concepto`, `Descripción`, `Detalle`) and either a signed amount column (such as `Importe`, `Amount`) or separate debit and credit columns (`Debe`/`Haber`, `Cargo`/`Abono`). Dates SHALL be accepted as `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY` or `DD/MM/YY`, and amounts with comma or dot as decimal separator. There is no manual column mapping.

#### Scenario: Unrecognized header
- **WHEN** the file has no recognizable header
- **THEN** the system rejects it with a validation error explaining the problem

#### Scenario: Separate debit and credit columns
- **WHEN** the file has `Debe` and `Haber` columns instead of a signed amount
- **THEN** each row gets a single signed amount, negative for debits and positive for credits

### Requirement: Preview classifies every row against existing transactions
Each row SHALL be classified against the account's non-deleted transactions within the file's date range (±1 day) as `EXACT_DUPLICATE` (same date, amount and description, compared through a hash of account, date, amount and normalized description), `PROBABLE_DUPLICATE` (same amount, date within ±1 day and description at least 85% similar) or `NEW`, with the matched transaction for duplicates. A previewed import SHALL be retrievable again by its id.

#### Scenario: Exact duplicate detection
- **WHEN** a row has the same date, amount and description as an existing transaction of the account
- **THEN** the row is classified `EXACT_DUPLICATE` and points to that transaction

#### Scenario: Probable duplicate
- **WHEN** a row has the same amount as an existing transaction one day apart and a slightly different description
- **THEN** the row is classified `PROBABLE_DUPLICATE`

### Requirement: Commit applies a user-chosen strategy and never touches manual transactions
On commit the user SHALL choose a strategy:
- `append_new` (default): insert the `NEW` rows plus the duplicate rows the user explicitly selected; delete nothing.
- `replace_range`: move to the trash the account's previously imported transactions within the file's date range and insert all the rows of the file.
- `replace_selected`: move to the trash the imported transactions matched by the selected rows, and insert the `NEW` rows plus the selected ones.

Transactions recorded manually SHALL never be moved to the trash by an import. Inserted transactions SHALL have `source = 'import'`, keep the statement concept as their description, and be categorized with the categorization rules (or "Sin Clasificar"). An import SHALL be committed at most once, and the result SHALL report how many transactions were inserted, replaced and skipped. After the commit the system SHALL re-evaluate the current month's budget notifications.

#### Scenario: Append only new rows
- **WHEN** the user commits with `append_new` a file with 12 new rows and 38 exact duplicates
- **THEN** 12 transactions are created and 38 rows are skipped

#### Scenario: Replace range preserves manual movements
- **WHEN** the user commits with `replace_range` a file covering a month where they also have manual cash expenses
- **THEN** the previously imported transactions of that range go to the trash, all rows are inserted, and the manual expenses are untouched

#### Scenario: Double commit is rejected
- **WHEN** the user commits an import that is already committed
- **THEN** the system rejects the request with a conflict error
