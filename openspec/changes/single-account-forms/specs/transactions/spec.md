## ADDED Requirements

### Requirement: The account is only asked for when the user has several accounts
When the user has exactly one account, the app SHALL NOT show an account field in the «Agregar movimiento» form, in the «Importar estado de cuenta» form or in the dashboard, and SHALL use that account automatically. When the user has more than one account, the movement form SHALL show the account field with the first account preselected, the import form SHALL ask the user to choose an account, and the dashboard SHALL offer «Todas las cuentas» plus each account.

#### Scenario: Add a movement with one account
- **WHEN** a user with a single account opens «Agregar movimiento» and saves an expense
- **THEN** no «Cuenta» field is shown and the expense is recorded on that account

#### Scenario: Import with one account
- **WHEN** a user with a single account chooses a CSV file to import
- **THEN** no «Cuenta» field is shown and the upload button is enabled without choosing an account

#### Scenario: Several accounts
- **WHEN** a user with two accounts opens the import form
- **THEN** the «Cuenta» field is shown starting at «Selecciona una cuenta»
