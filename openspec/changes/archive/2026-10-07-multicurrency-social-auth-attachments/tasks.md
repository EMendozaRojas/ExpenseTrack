<!-- Revisado 2026-10-07 antes de archivar: el borrador se implementó como un único change en tres partes (commits 40b7fd0, f4548a3 y 836a836), más simple que lo planificado. Las tareas reflejan lo implementado; lo demás figura en "Diferido". -->

## 1. Preferencias y multimoneda

- [x] 1.1 `app/models/user_preference.py` (1:1 con `User`, `base_currency` y `locale`, creada al primer uso) y `app/models/fx_rate.py`; migración
- [x] 1.2 `GET`/`PATCH /users/me/preferences`; moneda base bloqueada si hay movimientos; tests
- [x] 1.3 `GET`/`POST /fx-rates` con tipos de cambio cargados a mano; `app/services/fx.py` con tipo directo o inverso del día; tests
- [x] 1.4 Columnas `currency`, `fx_rate_to_account_currency` y `amount_in_account_currency` en `transactions`; conversión al registrar un movimiento en otra moneda (422 sin tipo de cambio); tests
- [x] 1.5 Frontend: moneda base configurable en Configuración

## 2. Login social y refresh tokens

- [x] 2.1 `app/models/auth_identity.py`; `users.hashed_password` nullable; migración
- [x] 2.2 Refresh tokens con hash en base de datos, `POST /auth/refresh` con rotación y `POST /auth/logout` con revocación; tests
- [x] 2.3 Google OAuth (`/auth/oauth/google/start` y `/callback`) con `state` firmado, 503 sin configurar, ligado automático por email; tests con Google simulado
- [x] 2.4 Frontend: botón "Entrar con Google" y pantalla de callback

## 3. Adjuntos

- [x] 3.1 `app/services/storage.py` con backend local en el volumen `attachments_data`
- [x] 3.2 `app/models/attachment.py` + migración; `POST /transactions/{id}/attachments`, `GET`/`DELETE /attachments/{id}` y listado por movimiento (JPEG/PNG/WebP/PDF, ≤10 MB); tests de tipo, tamaño y aislamiento
- [x] 3.3 Frontend: panel de adjuntos en el detalle del movimiento

## Diferido

Del borrador original, no implementado:

- Descarga diaria de tipos de cambio del BCE y uso del último tipo anterior marcado como aproximado
- Conversión de las estadísticas a la moneda base (`convert_to`)
- Zona horaria y primer día de la semana en preferencias
- Ligado de una identidad de Google a una cuenta con contraseña pidiendo antes la contraseña (se liga automáticamente por email)
- Verificación del `id_token` con JWKS mediante `authlib`
- Smoke del plan original (estadísticas convertidas)

## Hallazgo al revisar (2026-10-07)

- El saldo de una cuenta suma el importe original de cada movimiento, no `amount_in_account_currency`: un gasto en USD sobre una cuenta en EUR descontaría el importe en dólares. No afecta en la práctica: la app no ofrece registrar movimientos en otra moneda y no hay datos así. Aclarado con el usuario: la multimoneda deseada son cuentas independientes por moneda, sin conversión. El cambio está planteado en la ficha `independent-currency-accounts` (mejora futura, fuera del MVP).
