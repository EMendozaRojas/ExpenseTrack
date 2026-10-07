# social-auth Specification

## Purpose
Inicio de sesión con Google además de email y contraseña, ligando la identidad de Google a la cuenta con el mismo email, y tokens de acceso de corta duración con refresh tokens rotativos y revocables.

## Requirements

### Requirement: User can sign in with Google
The system SHALL support signing in with Google through an authorization-code flow completed on the server, protected by a signed `state` value. When Google credentials are not configured, starting the flow SHALL respond as service unavailable. After a successful sign-in the system SHALL redirect to the frontend with an access token and a refresh token.

#### Scenario: First sign-in with a new email
- **WHEN** a user completes the Google flow with an email that has no account
- **THEN** the system creates a user without a password, stores the Google identity and redirects with the tokens

#### Scenario: Returning Google user
- **WHEN** a user completes the flow and that Google identity is already linked
- **THEN** the system signs them into the linked account

#### Scenario: Invalid state
- **WHEN** the callback receives an invalid or expired `state`
- **THEN** the system rejects it with a bad request error

#### Scenario: Not configured
- **WHEN** Google credentials are not configured and the user starts the flow
- **THEN** the system responds as service unavailable

### Requirement: A Google email matching an existing account links to it
When the email returned by Google matches an existing account, the system SHALL link the Google identity to that account and sign the user in, without creating a second account (Google verifies email ownership). Accounts created only through Google SHALL have no password and SHALL NOT be able to log in with email and password.

#### Scenario: Email of an existing password account
- **WHEN** Google returns the email of an existing account registered with a password
- **THEN** the identity is linked to that account and the user is signed in, and no second account is created

#### Scenario: Password login for a Google-only account
- **WHEN** a user created through Google tries to log in with email and password
- **THEN** the system rejects the login

### Requirement: Access tokens are short-lived with revocable, rotating refresh
The system SHALL issue a short-lived access token and a refresh token on login. Exchanging a valid refresh token SHALL return a new access token and a new refresh token and revoke the one used. Logout SHALL revoke the refresh token. A revoked or expired refresh token SHALL NOT yield new tokens.

#### Scenario: Refresh rotates the token
- **WHEN** the client exchanges a valid refresh token
- **THEN** the system issues new tokens and the old refresh token stops working

#### Scenario: Logout revokes refresh
- **WHEN** the user logs out and then tries to refresh with the same token
- **THEN** the system rejects the refresh
