<!-- BORRADOR PROVISIONAL: primero resolver D0 en design.md (¿un cambio o tres?). El resto depende de D1-D8. Revisar antes de /opsx:apply. -->

## 1. Preferencias y multi-moneda

- [ ] 1.1 `app/models/user_preference.py` (1:1 con `User`) + `app/models/fx_rate.py`; migración; data-migration que crea preferencias `EUR` para usuarios existentes
- [ ] 1.2 Crear `user_preferences` al registrar; `PATCH /users/me/preferences` + `app/routers/preferences.py`; tests
- [ ] 1.3 `app/services/fx.py`: fetch diario de tasas BCE (mismo mecanismo de job que presupuestos), fallback a última tasa previa con marca de aproximado; tests
- [ ] 1.4 Columnas `original_currency`, `original_amount`, `fx_rate` en `transactions`; conversión al registrar movimiento en moneda distinta a la de la cuenta; tests de saldo
- [ ] 1.5 Parámetro `convert_to` en los endpoints de `stats` (conversión a fecha de cada movimiento); tests
- [ ] 1.6 Frontend: formateo con `Intl.NumberFormat` según preferencias; pantalla de ajustes regionales

## 2. Auth social

- [ ] 2.1 Tests de regresión del login por contraseña actual (red de seguridad antes de tocar auth)
- [ ] 2.2 `app/models/auth_identity.py`; `users.hashed_password` → nullable; migración (downgrade falla si hay nulos)
- [ ] 2.3 Refresh tokens: modelo (hash en DB), `POST /auth/refresh` con rotación, `POST /auth/logout` con revocación; tests
- [ ] 2.4 OAuth con `authlib`: `GET /auth/oauth/{provider}/start` y `/callback` (Google), verificación de `id_token` vía JWKS, validación de `state`; secretos en `.env(.example)`; tests con proveedor simulado
- [ ] 2.5 Flujo de ligado por colisión de email (D5); test: email existente con contraseña no crea cuenta duplicada
- [ ] 2.6 Frontend: botón "Entrar con Google", pantalla de callback, flujo de ligado

## 3. Adjuntos

- [ ] 3.1 `app/services/storage.py`: interfaz `StorageBackend` + `LocalStorage` (volumen, ruta `{owner_id}/{uuid}{ext}`); tests
- [ ] 3.2 `app/models/attachment.py` + migración; volumen `attachments_data` en `docker-compose.yml`
- [ ] 3.3 `app/routers/attachments.py`: `POST /transactions/{id}/attachments` (multipart, valida mime real y tamaño), `GET /attachments/{id}` (stream con auth + pertenencia), `DELETE /attachments/{id}`; tests (tipo no permitido, no-dueño → 404, borrado elimina fichero)
- [ ] 3.4 Frontend: subir y previsualizar recibo en el detalle de movimiento

## 4. Verificación

- [ ] 4.1 Backend `ruff`/`mypy`/`pytest --cov` (≥70%); Frontend `eslint`/`tsc`/`vitest --coverage` (≥70%)
- [ ] 4.2 Smoke: cambiar moneda base y ver stats convertidos; registrar gasto en USD sobre cuenta EUR; login con Google en una cuenta nueva y ligado en una existente; adjuntar un recibo y descargarlo; intentar descargarlo como otro usuario (404)
