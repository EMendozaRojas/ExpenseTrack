## Purpose

Alta e inicio de sesión mediante proveedores de identidad externos además de email/contraseña, ligando la identidad externa a una cuenta existente cuando el email ya está en uso, y emitiendo tokens de acceso cortos con refresco revocable.

## ADDED Requirements

### Requirement: User can sign in with an external provider
The system SHALL support authenticating via a configured external provider using an authorization-code flow completed on the server, verifying the provider's identity token before issuing application tokens.

#### Scenario: First sign-in with a new email
- **WHEN** a user completes the provider flow with an email that has no existing account
- **THEN** the system creates a user with no password, stores the external identity, and issues application tokens

#### Scenario: Returning social user
- **WHEN** a user completes the provider flow and that external identity is already linked to an account
- **THEN** the system signs them into that account

### Requirement: Existing email requires linking, not a duplicate account
When the provider's email matches an existing account that has a password and no link to this identity, the system SHALL NOT sign the user in automatically; it SHALL require authenticating with the existing credentials to link the identity.

#### Scenario: Email collision with a password account
- **WHEN** the provider returns an email that belongs to an existing password-based account
- **THEN** the system asks the user to authenticate with their password to link the external identity, and does not create a second account

### Requirement: Access tokens are short-lived with revocable refresh
The system SHALL issue a short-lived access token and a refresh token that can be exchanged for a new access token and revoked on logout. A revoked refresh token SHALL NOT yield new access tokens.

#### Scenario: Refresh
- **WHEN** the client exchanges a valid, non-revoked refresh token
- **THEN** the system issues a new access token

#### Scenario: Logout revokes refresh
- **WHEN** the user logs out and then tries to refresh with the same token
- **THEN** the system rejects the refresh
