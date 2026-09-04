## Context

Ver `proposal.md` — Why. Depende de `accounts-and-transactions`. Agrupa tres capacidades independientes; **podría partirse en tres cambios** si en la revisión se prefiere (ver D0). Estado actual: auth solo email/contraseña, JWT sin refresh, sin adjuntos, sin preferencias, todo asume EUR implícito. Este documento recoge las **decisiones abiertas**.

## Goals / Non-Goals

**Goals:**
- Preferencias regionales por usuario y formato de importes coherente.
- Movimientos en varias monedas con tasa fechada y conversión opcional.
- Login con Google (al menos) sin romper el login por contraseña ni duplicar cuentas.
- Adjuntar recibos de forma segura y portable.

**Non-Goals:**
- Integración con agregadores bancarios (PSD2).
- Reconciliación de FX en tiempo real / intradía.
- Más proveedores que los que se decidan (Apple, GitHub… quedan para después).
- OCR del recibo adjunto.

## Decisions

### D0 — ¿Un cambio o tres?
- Este documento cubre los tres. Alternativa: `user-preferences-and-multicurrency`, `social-auth`, `receipt-attachments` por separado, más fáciles de revisar y desplegar.
- **PENDIENTE DE DECIDIR EN LA REVISIÓN.** Si se parte, este change se archiva y se crean los tres.

### D1 — Fuente y cadencia de tasas FX
- Propuesto: BCE (referencia diaria, gratis, sin API key), un fetch/día vía el mismo mecanismo de job que los presupuestos (D del cambio de presupuestos). Guardar `rate` por `(date, base, quote)`.
- Días sin publicación (findes/festivos): usar la última tasa disponible.
- **PENDIENTE DE DECIDIR** monedas soportadas (todas las del BCE vs una lista corta) y qué hacer si falta la tasa de una fecha antigua al importar histórico.

### D2 — Dónde se fija la moneda de un movimiento
- Propuesto: un movimiento hereda la `currency` de su cuenta; solo si el extracto/ئusuario indica otra, se guarda `original_currency` + `original_amount` + `fx_rate` + `amount` ya convertido a la moneda de la cuenta.
- **PENDIENTE DE CONFIRMAR** si el MVP necesita movimientos multi-moneda dentro de una cuenta o basta con "una cuenta = una moneda".

### D3 — Conversión en `stats`
- `convert_to=<ccy>` opcional: además de los totales por moneda, un total convertido usando la tasa de la **fecha de cada movimiento** (no la de hoy). Sin el parámetro, comportamiento actual (por moneda).
- **PENDIENTE DE CONFIRMAR** que la conversión es "a fecha del movimiento" y no "a fecha de fin de rango".

### D4 — Proveedores OAuth y verificación
- Propuesto: Google primero (OpenID Connect, verificación de `id_token` con JWKS). `authlib` para el flujo.
- Redirect URIs y credenciales en `.env` (no versionadas); en local `http://localhost:5173/oauth/callback`.
- **PENDIENTE DE DECIDIR** si se hace flujo con backend (code exchange en el servidor, recomendado) o PKCE en el frontend.

### D5 — Ligado de identidades y colisión de email
- Si el email del proveedor coincide con un usuario existente **con contraseña**: no se inicia sesión automáticamente; se pide autenticar con la contraseña para ligar la identidad (`auth_identities`).
- Si coincide con un usuario que ya tiene esa identidad: login normal.
- Si no existe: se crea usuario con `hashed_password NULL` y la identidad.
- **PENDIENTE DE CONFIRMAR** el flujo exacto de ligado (¿en la misma pantalla de callback? ¿email de confirmación?).

### D6 — Refresh tokens
- Propuesto: access token corto (p. ej. 15 min) + refresh token opaco persistido (hash en DB) con expiración larga y revocación en `logout`; rotación en cada uso.
- **PENDIENTE DE DECIDIR** almacenamiento del refresh en el frontend (cookie httpOnly vs memoria + `localStorage`) — afecta a CSRF y a la config de CORS actual.

### D7 — Almacenamiento de adjuntos
- Propuesto: `StorageBackend` con implementación local `LocalStorage` que escribe en un volumen (`/data/attachments/{owner_id}/{uuid}{ext}`); `storage_key` guarda la ruta relativa. Interfaz lista para una implementación S3-compatible.
- Servir siempre por endpoint con `get_current_user` + comprobación de pertenencia; nunca ruta estática.
- **PENDIENTE DE FIJAR:** tamaño máx (p. ej. 10 MB), mimes permitidos (`image/jpeg`, `image/png`, `image/webp`, `application/pdf`), y si se generan miniaturas.

### D8 — Formato de importes en el frontend
- `Intl.NumberFormat(locale, {style:'currency', currency})` con los valores de `user-preferences`. El backend sigue enviando importes como string decimal + código de moneda; el formateo es del frontend.
- **PENDIENTE DE CONFIRMAR.**

## Risks / Trade-offs

- [Cambiar `hashed_password` a nullable + refresh tokens toca el núcleo de auth] → cubrir con tests de regresión del login por contraseña antes de tocar nada; hacerlo detrás de los tests existentes verdes.
- [OAuth mal configurado filtra o bloquea el acceso] → flujo con code exchange en backend, validar `state`, verificar `id_token` con JWKS, secretos solo en `.env`.
- [Adjuntos: subida de archivos peligrosos / path traversal] → validar mime real (no solo extensión), nombre de archivo generado (uuid), límite de tamaño, servir con `Content-Disposition: attachment` y sin ejecutar nada.
- [FX faltante para fechas antiguas] → política de fallback (última tasa previa) documentada; marcar el movimiento si se usó una tasa aproximada.
- [Agrupar 3 capacidades infla el cambio] → D0 permite partirlo.

## Migration Plan

1. Esquema: `user_preferences` (fila por usuario, creada al registrarse y backfill para los existentes con defaults), `fx_rates`, `auth_identities`, `attachments`; `users.hashed_password` → nullable; `transactions` gana `original_currency`, `original_amount`, `fx_rate` (nullable).
2. Data-migration: crear `user_preferences` con `base_currency='EUR'` para todos los usuarios actuales.
3. Infra: volumen `attachments_data` en `docker-compose.yml`; variables OAuth y de FX en `.env.example`.
4. Rollback: `downgrade` elimina tablas/columnas nuevas; `hashed_password` vuelve a `NOT NULL` solo si no hay filas nulas (si las hay, el downgrade falla a propósito).

## Open Questions

- ¿Se permite al usuario cambiar `base_currency` una vez tiene datos? Implica re-mostrar todo convertido; no cambia el almacenamiento.
- ¿Retención/borrado de adjuntos al borrar (soft) un movimiento? Propuesto: se conservan hasta el borrado definitivo del movimiento.
- ¿Se soporta más de una identidad social por usuario? El modelo `auth_identities` ya lo permite; la UI puede limitarlo.
