## ADDED Requirements

### Requirement: Tests are isolated from development data and email
Running the backend test suite SHALL use its own database, recreated and migrated to the latest revision at the start of each run, and SHALL NOT read or modify the development database. Email sending SHALL be disabled while the tests run, whatever the environment configuration says.

#### Scenario: Running the tests
- **WHEN** a developer runs `pytest` in the backend container
- **THEN** the tests run against `<database>_test` and the development database is left unchanged

#### Scenario: SMTP configured in the environment
- **WHEN** `SMTP_HOST` points to a mail server and the tests trigger a notification
- **THEN** no email is sent

#### Scenario: Isolation broken
- **WHEN** the test settings point to a database whose name does not end in `_test`, or SMTP is enabled
- **THEN** the test suite fails with an explicit message
