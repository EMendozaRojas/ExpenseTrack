## ADDED Requirements

### Requirement: Code quality and dependencies are checked on every push
The repository SHALL pass its declared quality tools with no warnings: ruff lint and format, mypy in strict mode, ESLint and Prettier. A continuous integration workflow SHALL run them, together with the backend and frontend test suites, a production build and a dependency vulnerability audit, on every push and pull request. Pre-commit hooks SHALL run the same tools locally using the project's containers when they need project dependencies.

#### Scenario: Push with a formatting problem
- **WHEN** a commit with an unformatted Python file is pushed
- **THEN** the CI workflow fails on the format check

#### Scenario: Known vulnerability in a dependency
- **WHEN** a backend dependency has a published vulnerability
- **THEN** the CI dependency audit fails

#### Scenario: Clean repository
- **WHEN** the CI runs on the current `main`
- **THEN** every job passes
