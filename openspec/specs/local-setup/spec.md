# local-setup Specification

## Purpose
Cómo se levanta el proyecto en local y qué garantías da: migraciones aplicadas al arrancar y autocontenidas, tests aislados de los datos de desarrollo y del correo, y calidad comprobada en cada push.

## Requirements

### Requirement: The app starts from a clean install following the README
Starting the stack with `cp .env.example .env && docker compose up --build` on an empty database SHALL leave the application usable without extra manual steps: the backend SHALL apply all pending database migrations before serving requests, and SHALL NOT start if a migration fails.

#### Scenario: First start on an empty database
- **WHEN** a developer clones the repository and starts the stack following the README with no existing database volume
- **THEN** the migrations run to the latest revision and registering a user succeeds

#### Scenario: Start with an up-to-date database
- **WHEN** the backend starts and the database is already at the latest revision
- **THEN** no migration runs and the API starts normally

### Requirement: Migrations do not depend on application code that changes
Each migration SHALL contain the data it seeds or transforms, frozen as it was when the migration was written, and SHALL NOT import seed data from the application package. A test SHALL apply every migration to an empty database and check the resulting schema and system data.

#### Scenario: Seed data changes later
- **WHEN** the category seed in the application code is edited
- **THEN** applying all migrations to an empty database still succeeds and produces the same system categories as before

#### Scenario: Migration chain broken
- **WHEN** a change breaks applying the migrations from an empty database
- **THEN** the test suite fails

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
