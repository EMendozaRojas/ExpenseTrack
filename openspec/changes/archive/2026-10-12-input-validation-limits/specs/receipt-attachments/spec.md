## ADDED Requirements

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
