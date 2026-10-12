## ADDED Requirements

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
