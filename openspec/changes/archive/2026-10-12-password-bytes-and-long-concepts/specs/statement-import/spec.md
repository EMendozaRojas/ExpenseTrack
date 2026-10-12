## ADDED Requirements

### Requirement: Long statement descriptions are shortened, not rejected
When a statement row has a description longer than 255 characters, the system SHALL keep its first 255 characters and import the row normally; the preview, duplicate detection and the created transaction SHALL all use the shortened text.

#### Scenario: Description of 300 characters
- **WHEN** a user uploads a CSV with a row whose description has 300 characters
- **THEN** the preview lists that row with a 255-character description and confirming the import creates the transaction
