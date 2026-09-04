## Purpose

Permite a un usuario autenticado cargar un extracto bancario en archivo, revisar el parseo y el mapeo de columnas, ver cómo se solapa con lo que ya tiene registrado, y confirmar la importación eligiendo una estrategia de reconciliación que nunca destruye sus movimientos manuales ni el trabajo de categorización previo.

## ADDED Requirements

### Requirement: User uploads a statement file against one of their accounts
The system SHALL accept a file upload (CSV or XLSX) associated with an account the user owns, create an import batch in `pending` state, and parse the file asynchronously without blocking the upload response. Files above the configured size or row limit SHALL be rejected with a clear error.

#### Scenario: Upload starts an async import
- **WHEN** the user uploads a CSV against their account
- **THEN** the system stores the file, returns an import batch with status `pending`, and parses it in the background

#### Scenario: Upload against another user's account
- **WHEN** the user uploads a file targeting an account they do not own
- **THEN** the system responds with a "not found" error and creates no batch

#### Scenario: Oversized file
- **WHEN** the user uploads a file exceeding the size or row limit
- **THEN** the system rejects it with an error explaining the limit and creates no batch

### Requirement: Parsed rows are normalized and column mapping can be corrected
The system SHALL detect delimiter, decimal separator, date format and encoding, and normalize each row to a signed decimal amount and an ISO date. It SHALL derive a source signature from the file's own structure (the header column names and any issuer text). When a mapping saved for that user and source signature exists, the system SHALL apply it automatically and advance the batch straight to `needs_review`. Otherwise, when the mapping is ambiguous, the batch SHALL enter `needs_mapping` and the user SHALL be able to submit an explicit column mapping, which the system SHALL save against that source signature for future imports. A user-submitted correction SHALL update the saved mapping.

#### Scenario: Ambiguous columns require mapping
- **WHEN** parsing cannot determine which columns hold date, amount and concept and no saved mapping matches the source signature
- **THEN** the batch status becomes `needs_mapping` and no transactions are created yet

#### Scenario: Known source signature auto-applies its mapping
- **WHEN** the user uploads a file whose source signature matches a mapping they previously confirmed
- **THEN** the system applies that mapping and the batch goes directly to `needs_review` without a `needs_mapping` step

#### Scenario: User supplies or corrects a mapping
- **WHEN** the user submits a column mapping for a batch
- **THEN** the system re-parses using that mapping, advances the batch to `needs_review`, and saves the mapping against the batch's source signature (replacing any prior one)

#### Scenario: Separate debit/credit columns
- **WHEN** the statement has separate debit and credit columns
- **THEN** the system produces one signed amount per row (negative for debit, positive for credit)

### Requirement: Review classifies every row and reports range overlap
For a parsed batch the system SHALL report the file's date range for the target account, how many existing non-deleted transactions fall in that range (split into imported vs manual), and a per-row classification: `NEW`, `EXACT_DUPLICATE` (same `external_hash`), `PROBABLE_DUPLICATE` (same account, date and amount, similar description), `CONFLICT` (same account, date and amount but the file carries new data), or `MISSING_FROM_FILE` (present in the range in the system, absent from the file).

#### Scenario: Overlap summary
- **WHEN** the user opens the review of a parsed batch
- **THEN** the system returns the file date range, the count of existing transactions in that range, and counts per row classification

#### Scenario: Exact duplicate detection
- **WHEN** a file row has the same `external_hash` as an existing non-deleted transaction on the account
- **THEN** that row is classified `EXACT_DUPLICATE`

### Requirement: Commit applies a user-chosen reconciliation strategy atomically
The system SHALL commit a batch only on explicit request with one of three strategies, in a single database transaction:
- `append_new`: insert only `NEW` rows; leave every existing transaction untouched.
- `replace_range`: soft-delete the account's transactions in the file's date range whose `source` is `import` or `rule` (never `manual`), marking them with the batch id; insert all file rows. Transfer legs are `manual` and are therefore never touched. Before deleting, carry over `category_id`, splits and note to the matching incoming row: automatically for an exact (`external_hash`) match, and for a fuzzy (`PROBABLE_DUPLICATE`) match only when the user marked that row as a duplicate in the review.
- `replace_selected`: behave as `append_new` except for rows the user explicitly marks to take from the file.
On commit the system SHALL record the strategy and the counts of inserted, replaced and skipped rows, plus `receipts_not_carried_over` (receipts on replaced transactions with no heir), and SHALL run categorization rules on the newly inserted transactions. A batch already `committed` SHALL NOT be committed again.

#### Scenario: Append only new rows
- **WHEN** the user commits with `append_new` and the batch has 12 `NEW` and 38 `EXACT_DUPLICATE` rows
- **THEN** the system inserts 12 transactions, changes nothing else, and reports 12 inserted / 0 replaced / 38 skipped

#### Scenario: Replace range preserves manual movements and transfers
- **WHEN** the user commits with `replace_range` for January and the account has 40 imported transactions, 2 manual cash transactions and 1 transfer leg in January
- **THEN** the 40 imported transactions are soft-deleted and replaced from the file, and the 2 manual transactions and the transfer leg remain untouched

#### Scenario: Replace range carries over categorization on an exact match
- **WHEN** an incoming row is an exact-hash match of a to-be-replaced transaction that had a manually assigned category
- **THEN** the new transaction keeps that category automatically

#### Scenario: Replace range does not carry over an unconfirmed fuzzy match
- **WHEN** an incoming row is only a fuzzy match of a to-be-replaced transaction and the user did not mark it as a duplicate
- **THEN** the new transaction is inserted without inheriting the old category, and the old transaction is soft-deleted

#### Scenario: Orphan receipt is retained and reported
- **WHEN** a replaced transaction had a receipt and no incoming row inherits it
- **THEN** the receipt stays attached to the soft-deleted transaction and the commit result reports it in `receipts_not_carried_over`

#### Scenario: Double commit is rejected
- **WHEN** the user commits a batch that is already `committed`
- **THEN** the system rejects the request and makes no further changes

### Requirement: A committed import can be undone
The system SHALL allow reverting a committed batch: transactions it inserted are soft-deleted and transactions it soft-deleted via `replace_range` are restored.

#### Scenario: Undo a replace_range import
- **WHEN** the user undoes a batch committed with `replace_range`
- **THEN** the transactions that batch inserted are removed and the ones it had replaced are restored to their prior state
