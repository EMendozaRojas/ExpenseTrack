## ADDED Requirements

### Requirement: Invalid input is rejected, never answered with an internal error
Every API input SHALL be validated against the limits of where it is stored: text fields SHALL have a maximum length equal to their column, and amounts SHALL be smaller than one trillion in absolute value. Input outside those limits SHALL be rejected with 422 naming the field. If a value still reaches the database and is rejected there for its size or format, the API SHALL respond 422 «Los datos no son válidos» instead of an internal error.

#### Scenario: Text longer than its column
- **WHEN** a user creates a transaction whose `counterparty` has 300 characters
- **THEN** the system responds 422 indicating `counterparty`, and nothing is stored

#### Scenario: Amount too large
- **WHEN** a user creates an expense of `-1000000000000000`
- **THEN** the system responds 422 indicating `amount`

#### Scenario: Value rejected by the database
- **WHEN** a value without a schema limit is too large for its column
- **THEN** the system responds 422 instead of 500
