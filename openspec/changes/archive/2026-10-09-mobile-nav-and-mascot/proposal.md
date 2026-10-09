## Why

En el móvil, el menú lateral se convierte en una fila horizontal arriba con las 7 secciones y una letra diminuta: no caben, y Notificaciones y Configuración quedan fuera de la pantalla sin que nada indique que hay que deslizar. Además, las notificaciones aparecen dos veces: en el menú y en una campanita junto a «Cerrar sesión». La marca también es inconsistente: el logo (mascota con letras) solo se ve en el menú lateral del ordenador, desaparece en el móvil y no está en el inicio de sesión. La autora ha preparado una mascota nueva sin letras para usarla igual en todas las vistas.

Decisiones tomadas con la autora el 2026-10-09 sobre maquetas (opción B, logo 1, logo grande en el login, la misma mascota con movimiento en todas las vistas).

## What Changes

- **Móvil: barra de navegación abajo** con las 4 secciones principales (Estadísticas, Movimientos, Presupuestos, Metas) y un botón **«Más»** que abre un panel con Análisis, Notificaciones y Configuración. «Más» muestra el número de notificaciones sin leer.
- **Sin campanita en la barra de arriba**, en todas las vistas: el contador de notificaciones queda en el menú (ordenador) y en «Más» (móvil).
- **Mascota nueva** (sin letras) con el nombre «Expense**Track**» escrito al lado, con el mismo movimiento de rebote suave en las tres vistas:
  - ordenador: abajo del menú lateral, en lugar del logo actual;
  - móvil: pequeña, a la izquierda de la barra de arriba;
  - inicio de sesión: grande, encima del formulario, con el lema «Tus gastos, siempre contigo».
- El movimiento se desactiva si el usuario tiene activada la opción de «reducir movimiento» de su sistema (accesibilidad).
- La imagen se sirve en una versión ligera (unos 270 KB) generada a partir de `Design System/logo sin fondo listo.png`, que se conserva como original.

### Fuera de alcance

- Cambios en el registro, la bienvenida (onboarding) u otras pantallas fuera del menú y el login.
- El logo con letras del README (`frontend/public/logo.png`) se mantiene.

## Capabilities

### New Capabilities

- `app-navigation`: cómo se navega por la app en ordenador y en móvil, dónde se muestran las notificaciones sin leer y dónde aparece la marca (mascota y nombre).

### Modified Capabilities

(ninguna)

## Impact

- **Frontend**: `components/AppLayout.tsx` (barra inferior y panel «Más» en móvil, sin campanita, mascota en el menú y en la barra superior), nuevo `components/MobileNav.tsx`, `features/auth/LoginPage.tsx` (mascota, nombre y lema), `index.css` (estilos de la barra inferior, el panel, la mascota y su animación), `public/mascota.png` (nueva). Tests de `AppLayout`, del nuevo `MobileNav` y del login.
- **Backend**: sin cambios.
- **Repositorio**: se versiona `Design System/logo sin fondo listo.png` (original de la mascota).
