## Why

La revisión técnica del 2026-10-11 (`informe-ExpenseTrack.md`, hallazgos 🟡) encontró dos problemas en la sesión:

- **El frontend nunca usa el refresh token.** El README promete «refresh tokens rotativos», pero ninguna parte del frontend llama a `/auth/refresh`: el refresh token solo se guarda y se usa al cerrar sesión. Cuando el token de acceso caduca (60 minutos), las peticiones empiezan a fallar con 401 y la sesión solo se limpia al recargar la página.
- **Tokens en la query string de la redirección de Google.** `access_token` y `refresh_token` viajan en `?…` de la URL, así que quedan en los logs del servidor del frontend y pueden salir en la cabecera *Referer*.

Acordado con la autora el 2026-10-12.

## What Changes

- **Renovación automática de la sesión**: si una petición con token recibe 401, el frontend pide un token nuevo con el refresh token y repite la petición una vez. Si varias peticiones fallan a la vez, se hace una sola renovación. Si la renovación falla, se cierra la sesión y se vuelve al login.
- **Tokens de Google en el fragmento**: la redirección al frontend pasa los tokens en `#…` (el navegador no envía el fragmento al servidor ni en el *Referer*), y la página de retorno los borra de la barra de direcciones en cuanto los lee.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `social-auth`: el frontend renueva la sesión con el refresh token y la redirección de Google no expone los tokens en la query.

## Impact

- **Frontend**: `api/client.ts` (nuevo `authorizedFetch` y registro de la renovación), `features/auth/AuthContext.tsx`, `features/auth/api.ts` (`refreshRequest`), `features/auth/SocialCallbackPage.tsx`, las subidas y descargas de `imports`, `attachments` y `profile`, y sus tests.
- **Backend**: `routers/auth.py` (redirección con fragmento), `tests/test_social_auth.py`.
- **Docs**: README (sección de autenticación, si aplica).
