## Why

En `OnboardingPage` el `useMutation` se llama después de un `return` anticipado (`if (user?.full_name) return <Navigate …/>`). Al guardar el nombre, `refreshUser()` actualiza el usuario y el componente se vuelve a renderizar: esta vez sale por el `return` antes de llamar a `useMutation`, React detecta menos hooks que en el render anterior y puede lanzar un error justo después de guardar, en lugar de llevar al usuario a la app. ESLint lo marca (`react-hooks/rules-of-hooks`). El test actual no lo detecta porque el usuario simulado nunca cambia tras guardar.

## What Changes

- Llamar a todos los hooks antes del `return` anticipado en `OnboardingPage` (sin cambiar lo que ve el usuario).
- Test de regresión: tras guardar, el usuario pasa a tener nombre y la pantalla redirige a la app sin errores.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

(ninguna: corrección interna sin cambio de comportamiento; no hay spec del onboarding)

## Impact

- **Frontend**: `features/profile/OnboardingPage.tsx` y su test.
- Elimina el único error de ESLint del proyecto.
