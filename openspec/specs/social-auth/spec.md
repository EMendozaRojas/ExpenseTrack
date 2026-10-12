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

### Requirement: The frontend renews the session with the refresh token
When a request made with an access token is answered with 401, the frontend SHALL exchange the stored refresh token for new tokens, store both, and repeat the request once with the new access token. Concurrent requests that fail at the same time SHALL share a single renewal. If there is no refresh token or the renewal fails, the frontend SHALL end the session locally and show the sign-in screen.

#### Scenario: Access token expired
- **WHEN** the access token has expired and the user opens a screen
- **THEN** the frontend renews the tokens and the screen loads normally

#### Scenario: Several requests at once
- **WHEN** three requests fail with 401 at the same time
- **THEN** a single call to `/auth/refresh` is made and the three requests are repeated with the new token

#### Scenario: Refresh token no longer valid
- **WHEN** the renewal responds 401
- **THEN** the session is cleared and the user is taken to the sign-in screen

### Requirement: Google sign-in does not expose tokens in the query string
After a successful Google sign-in, the redirect to the frontend SHALL carry the tokens in the URL fragment, never in the query string, and the frontend SHALL remove them from the address bar as soon as it reads them.

#### Scenario: Successful Google sign-in
- **WHEN** the Google callback succeeds
- **THEN** the redirect URL has no query parameters with tokens, the tokens are in the fragment, and after signing in the address bar no longer shows them
