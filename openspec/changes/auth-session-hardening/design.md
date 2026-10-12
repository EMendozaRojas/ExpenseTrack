## Context

- `apiFetch(path, token, init)` añade `Authorization` y lanza `ApiError` si la respuesta falla. Cinco llamadas (subir extracto, subir y descargar adjunto, subir y descargar avatar) usan `fetch` directamente con su propia cabecera.
- `AuthProvider` guarda `expensetrack_token` y `expensetrack_refresh_token` en `localStorage`; el token viaja por el contexto a cada llamada.
- `/auth/refresh` revoca el refresh token usado y devuelve uno nuevo (rotación): usar dos veces el mismo da 401.
- El callback de Google redirige a `/auth/social-callback?access_token=…&refresh_token=…`.

## Goals / Non-Goals

**Goals:** una sesión dura lo que dura el refresh token (30 días) sin errores al caducar el de acceso; los tokens no aparecen en la query de ninguna URL.

**Non-Goals:** mover los tokens a cookies `httpOnly` (cambio de arquitectura mayor; queda anotado como alternativa); sincronizar la sesión entre pestañas; código de un solo uso para el login social.

## Decisions

### D1 — La renovación vive en el cliente de la API
- `client.ts` exporta `authorizedFetch(url, token, init)`: hace la petición con `Authorization`; si la respuesta es 401 y había token, llama a la renovación registrada y, si obtiene un token nuevo, repite la petición **una sola vez** con él. `apiFetch` y las cinco llamadas directas pasan a usarla, así ninguna se queda sin renovación.
- `setSessionRefresher(fn)` registra la función que renueva. `AuthProvider` la registra al crearse (durante el primer render, no en un efecto, para que esté lista antes de las primeras peticiones de las pantallas hijas).
- **Una sola renovación a la vez**: mientras hay una en curso, las demás peticiones que reciben 401 esperan a esa misma promesa. Es necesario por la rotación: dos renovaciones en paralelo con el mismo refresh token harían que la segunda fallara y cerrara la sesión.
- Alternativa descartada: renovar con un temporizador antes de que caduque. No cubre el portátil que se suspende ni las pestañas en segundo plano, y añade estado.

### D2 — Qué hace `AuthProvider` al renovar
- Lee el refresh token de `localStorage`, llama a `POST /auth/refresh` (`refreshRequest`, sin token para no entrar en bucle), guarda los dos tokens nuevos y actualiza el token del contexto; las pantallas vuelven a pedir sus datos con él.
- Si no hay refresh token o la renovación falla, borra la sesión (como `logout`, sin llamar a la API) y la app vuelve al login.

### D3 — Fragmento en la redirección de Google
- Backend: `…/auth/social-callback#access_token=…&refresh_token=…`, con los valores codificados (`urlencode`).
- `SocialCallbackPage` lee `window.location.hash`, hace `history.replaceState` para quitar el fragmento de la barra de direcciones y del historial, y sigue como hasta ahora.
- Alternativa descartada por ahora: código de un solo uso canjeable por tokens. Es lo más robusto, pero requiere una tabla y un endpoint nuevos; el fragmento resuelve lo que señala la revisión (logs y *Referer*).

## Risks / Trade-offs

- [Los tokens siguen en `localStorage`] → un XSS podría leerlos; se mitiga con la validación de adjuntos (`nosniff`) y React escapando el contenido. Cookies `httpOnly` quedan como mejora futura.
- [Una petición no idempotente se repite tras renovar] → solo se repite si la primera respondió 401, es decir, si el backend no la procesó.

## Migration Plan

Sin migraciones. Las sesiones abiertas siguen funcionando: tienen ya su refresh token guardado.

## Open Questions

(ninguna)
