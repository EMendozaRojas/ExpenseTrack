<!-- Ficha de idea futura (2026-10-12): solo propuesta, no se implementa durante el MVP. Specs, design y tareas se escriben cuando se decida implementarla. -->

## Why

La revisión técnica del 2026-10-11 señala que `/auth/login` no limita los intentos: alguien podría probar contraseñas sin freno. Es aceptable en un MVP que solo corre en local, pero sería necesario antes de desplegar.

## What Changes

- Limitar los intentos fallidos de login por email y por IP (por ejemplo, 5 por minuto), respondiendo 429 con un mensaje claro.
- Mismo límite en `/auth/register` y `/auth/refresh`.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `social-auth`: límite de intentos en los endpoints de autenticación.

## Impact

- **Backend**: `routers/auth.py` y un contador (en Postgres o en memoria; habría que decidirlo).
- **Frontend**: mostrar el mensaje del 429 en el login.
