## ADDED Requirements

### Requirement: Registration enforces a minimum password and a normalized email
Registering with email and password SHALL require a password of 8 to 72 characters. Emails SHALL be stored and compared trimmed and in lowercase when registering, signing in with a password and signing in with Google, so that addresses differing only in case belong to the same account.

#### Scenario: Short password
- **WHEN** a user registers with the password `1234567`
- **THEN** the system responds 422 and creates no account

#### Scenario: Same email with different case
- **WHEN** `ana@example.com` is registered and someone registers `ANA@Example.com`
- **THEN** the system responds 409 «El email ya está registrado»

#### Scenario: Sign in with different case
- **WHEN** the user registered as `ana@example.com` signs in as ` Ana@Example.com`
- **THEN** the sign-in succeeds
