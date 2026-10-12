## MODIFIED Requirements

### Requirement: Registration enforces a minimum password and a normalized email
Registering with email and password SHALL require a password of at least 8 characters and at most 72 bytes in UTF-8 (the length bcrypt uses), so that no accepted password is silently truncated. Emails SHALL be stored and compared trimmed and in lowercase when registering, signing in with a password and signing in with Google, so that addresses differing only in case belong to the same account.

#### Scenario: Short password
- **WHEN** a user registers with the password `1234567`
- **THEN** the system responds 422 and creates no account

#### Scenario: Password longer than 72 bytes
- **WHEN** a user registers with a password of 72 «ñ» characters (144 bytes)
- **THEN** the system responds 422 explaining the limit in bytes, and creates no account

#### Scenario: Same email with different case
- **WHEN** `ana@example.com` is registered and someone registers `ANA@Example.com`
- **THEN** the system responds 409 «El email ya está registrado»

#### Scenario: Sign in with different case
- **WHEN** the user registered as `ana@example.com` signs in as ` Ana@Example.com`
- **THEN** the sign-in succeeds
