## Why

Tres capacidades de la visión quedan fuera del núcleo pero son diferenciadores para portafolio y para uso real: **multi-moneda** con preferencias regionales, **login social** (además de email/contraseña) y **adjuntar recibos** a los movimientos. Se agrupan porque son independientes entre sí, de riesgo acotado, y ninguna bloquea a las demás.

## What Changes

- **Preferencias y multi-moneda**:
  - Nuevo recurso `user-preferences`: `base_currency`, `locale`, `timezone`, inicio de semana, separador decimal. `PATCH /users/me/preferences`.
  - Tabla `fx_rates` (`date`, `base`, `quote`, `rate`) alimentada de una fuente diaria (BCE); cada movimiento en moteda distinta de la de su cuenta guarda la tasa usada.
  - Los endpoints de `stats` ganan un parámetro opcional `convert_to` que devuelve además el total convertido a la moneda base con la tasa de la fecha; sin el parámetro, siguen agregando por moneda.
- **Auth social**:
  - Tabla `auth_identities` (`user_id`, `provider`, `provider_uid`, `email`) separada de `users`; `users.hashed_password` pasa a nullable.
  - Flujo OAuth: `GET /auth/oauth/{provider}/start` y `/callback` (Google al menos). Si el email del proveedor ya existe con contraseña, se pide login para **ligar** la identidad, no se crea cuenta duplicada.
  - Refresh token + revocación (`POST /auth/refresh`, `POST /auth/logout`).
- **Adjuntos**:
  - Tabla `attachments` (`transaction_id`, `storage_key`, `filename`, `mime_type`, `size_bytes`). Fichero fuera de la DB, en volumen local vía una abstracción `StorageBackend` (migrable a S3-compatible).
  - `POST /transactions/{id}/attachments` (multipart, valida mime y tamaño), `GET /attachments/{id}` (stream con auth), `DELETE /attachments/{id}`.

## Capabilities

### New Capabilities
- `user-preferences`: ajustes regionales del usuario (moneda base, locale, zona horaria, formato) que condicionan cómo se agregan y se muestran los importes y los rangos de fecha.
- `multi-currency`: soporte de movimientos y cuentas en distintas monedas, con tasas de cambio fechadas y conversión opcional a la moneda base en las agregaciones.
- `social-auth`: alta e inicio de sesión mediante proveedores externos además de email/contraseña, con ligado de identidades a una cuenta existente y tokens de refresco revocables.
- `receipt-attachments`: adjuntar, descargar y borrar archivos de recibo asociados a un movimiento, almacenados fuera de la base de datos y servidos solo a su dueño.

### Modified Capabilities

(a concretar al archivar: `transactions` gana `currency` + tasa; `dashboard-stats` gana `convert_to`. No hay specs archivados todavía, así que se reflejará como MODIFIED en su momento.)

## Impact

- **Backend**: `app/models/user_preference.py`, `app/models/fx_rate.py`, `app/models/auth_identity.py`, `app/models/attachment.py`; `app/routers/preferences.py`, ampliación de `app/routers/auth.py`, `app/routers/attachments.py`; `app/services/fx.py` (fetch diario BCE), `app/services/storage.py` (`StorageBackend` local); OAuth con `authlib` o `httpx` + verificación de `id_token`.
- **Frontend**: pantalla de ajustes, botones de login social, subida/preview de recibo en el detalle de movimiento, formato de importes según `locale`/`base_currency`.
- **Dependencias nuevas**: `authlib` (o equivalente), cliente HTTP para FX (ya está `httpx` vía FastAPI), posiblemente `python-multipart` (ya presente).
- **Infra**: volumen para adjuntos en `docker-compose.yml`; variables OAuth en `.env`.
- **Orden**: depende de `accounts-and-transactions`; `multi-currency` se apoya en `dashboard-stats` si ya existe; las tres partes pueden implementarse por separado.
