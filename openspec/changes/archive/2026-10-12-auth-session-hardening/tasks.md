## 1. Renovación de la sesión (frontend)

- [x] 1.1 `client.ts`: `authorizedFetch` con reintento único tras 401, `setSessionRefresher` y una sola renovación en curso
- [x] 1.2 `apiFetch` y las cinco llamadas directas (`imports`, `attachments`, `profile`) usan `authorizedFetch`
- [x] 1.3 `auth/api.ts`: `refreshRequest`; `AuthProvider` registra la renovación, guarda los tokens nuevos y cierra la sesión si falla

## 2. Login con Google

- [x] 2.1 Backend: redirección con los tokens en el fragmento, codificados
- [x] 2.2 `SocialCallbackPage`: leer el fragmento y borrarlo de la URL

## 3. Tests

- [x] 3.1 `client.test.ts`: 401 → renueva y repite; renovación fallida → error; dos 401 a la vez → una sola renovación; sin token no renueva
- [x] 3.2 `AuthContext.test.tsx`: la renovación guarda los tokens nuevos; si falla, se cierra la sesión
- [x] 3.3 `SocialCallbackPage.test.tsx` y `test_social_auth.py` con el fragmento

## 4. Verificación

- [x] 4.1 `pytest`, `tsc`, `eslint`, `vitest` y Prettier en verde
- [x] 4.2 En el navegador: con un token de acceso caducado la app sigue funcionando y en `localStorage` aparece un refresh token nuevo
