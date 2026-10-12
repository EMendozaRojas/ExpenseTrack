## ADDED Requirements

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
