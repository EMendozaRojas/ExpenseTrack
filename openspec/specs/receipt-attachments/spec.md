# receipt-attachments Specification

## Purpose
Adjuntar, descargar y borrar archivos de recibo asociados a un movimiento de un usuario autenticado, con el binario almacenado fuera de la base de datos y accesible solo para el dueño del movimiento.

## Requirements

### Requirement: User can attach a receipt to their transaction
The system SHALL allow the owner of a transaction to upload one or more receipt files, validating the file type (JPEG, PNG, WebP or PDF) and rejecting files above 10 MB or empty files. The binary SHALL be stored outside the database; the database SHALL keep only metadata and a storage key.

#### Scenario: Attach a valid receipt
- **WHEN** the owner uploads a JPEG within the size limit to their transaction
- **THEN** the system stores the file, records its metadata linked to the transaction, and returns the attachment reference

#### Scenario: Reject a disallowed type
- **WHEN** the user uploads a file whose type is not in the allowed list
- **THEN** the system rejects it and stores nothing

#### Scenario: Attach to another user's transaction
- **WHEN** the user uploads a receipt to a transaction they do not own
- **THEN** the system responds with a "not found" error

### Requirement: Receipts are served only to their owner
The system SHALL serve an attachment's file only through an authenticated endpoint after verifying the requester owns the underlying transaction. Attachments SHALL NOT be reachable via a public static path.

#### Scenario: Owner downloads
- **WHEN** the owner requests their attachment
- **THEN** the system streams the file back

#### Scenario: Non-owner is denied
- **WHEN** a user requests an attachment belonging to another user's transaction
- **THEN** the system responds with a "not found" error

### Requirement: User can delete an attachment
The system SHALL allow the owner to delete an attachment, removing both its stored file and its metadata.

#### Scenario: Delete
- **WHEN** the owner deletes one of their attachments
- **THEN** the metadata and the stored file are both removed

### Requirement: Attachments are what they claim and download with any name
The system SHALL accept an attachment or avatar only if its content starts with the signature of an allowed type (JPEG, PNG, WebP or, for attachments, PDF) matching the declared type, and SHALL respond 415 otherwise. Downloads SHALL work for file names with any Unicode character, encoding the name in the `Content-Disposition` header, and SHALL include `X-Content-Type-Options: nosniff`. Names longer than 255 characters SHALL be shortened keeping the extension.

#### Scenario: Unicode file name
- **WHEN** a user uploads `recibo_日本.png` and downloads it
- **THEN** the download responds 200 with the original name in `filename*`

#### Scenario: Content does not match the declared type
- **WHEN** a user uploads an HTML file declared as `image/png`
- **THEN** the system responds 415 and stores nothing

#### Scenario: Very long name
- **WHEN** a user uploads a PDF whose name has 300 characters
- **THEN** the attachment is stored with a name of at most 255 characters ending in `.pdf`
