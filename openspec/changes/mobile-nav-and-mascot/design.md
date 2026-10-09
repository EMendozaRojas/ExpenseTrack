## Context

`AppLayout.tsx` pinta un menú lateral (`.app-sidebar`) con `NAV_ITEMS` (7 secciones, icono emoji + texto, contador en Notificaciones), el perfil arriba y `/logo.png` abajo con la animación `app-sidebar-logo-bounce`. La barra superior (`.app-topbar`) tiene una campanita (`NavLink` a `/notifications` con contador) y «Cerrar sesión». En `@media (max-width: 768px)` el menú lateral pasa a una fila horizontal con desplazamiento, oculta perfil y logo, y las etiquetas bajan a 0,65 rem. `LoginPage.tsx` no tiene marca. Maquetas aprobadas: artefacto «Menú móvil: dos opciones», fila «Propuesta final».

## Goals / Non-Goals

**Goals:** navegación cómoda en el móvil con todas las secciones alcanzables; una sola indicación de notificaciones por vista; la misma marca en ordenador, móvil y login.

**Non-Goals:** rediseñar otras pantallas; cambiar rutas; tocar el backend.

## Decisions

### D1 — Una lista de secciones, dos presentaciones
- `NAV_ITEMS` gana un campo `mobile: "bar" | "more"` (Estadísticas, Movimientos, Presupuestos y Metas → `bar`; Análisis, Notificaciones y Configuración → `more`), para que ordenador y móvil no se desincronicen.
- El menú lateral se sigue pintando igual; un componente nuevo `MobileNav` pinta la barra inferior y el panel «Más». La elección es solo CSS: en `> 768px` se oculta `MobileNav`; en `≤ 768px` se oculta el menú lateral. Alternativa descartada: detectar el ancho en JavaScript (`matchMedia`), que añade estado y parpadeos sin necesidad.
- Se mantienen los iconos emoji de `NAV_ITEMS` para no cambiar el estilo visual existente (las maquetas usaban iconos dibujados solo como boceto).

### D2 — Panel «Más»
- Botón con `aria-expanded` y `aria-controls`; el panel es un `<div role="dialog" aria-label="Más opciones">` sobre un fondo oscuro. Se cierra al elegir una sección, al tocar el fondo o con Escape (mismo patrón que `Modal`).
- «Más» se marca como activo si la ruta actual es de una sección `more`.
- Contador: el número de no leídas (`useUnreadCount`) en «Más» y en «Notificaciones» dentro del panel.

### D3 — Sin campanita
- Se elimina la campanita de la barra superior en todas las vistas. En el ordenador el contador sigue en el menú lateral; en el móvil, en «Más».

### D4 — Mascota
- `public/mascota.png`: copia ligera (600×400, unos 270 KB) de `Design System/logo sin fondo listo.png` (1536×1024, 1,8 MB), generada una vez y versionada. El original también se versiona.
- Componente pequeño `BrandMark` (`components/BrandMark.tsx`) con variantes `sidebar`, `topbar` y `hero` (login: con el lema), para no repetir marcado y estilos. Imagen con `alt=""` (decorativa) porque el nombre va escrito al lado.
- Animación: la de hoy (`translateY` + `rotate`, 2,2 s) renombrada a `mascot-bounce`, con menor recorrido en la barra superior del móvil (4 px). `@media (prefers-reduced-motion: reduce)` la desactiva.
- La barra superior del móvil muestra `BrandMark` a la izquierda y «Cerrar sesión» a la derecha; en el ordenador la marca no se repite arriba (ya está en el menú lateral).

### D5 — Detalles de la barra inferior
- `position: fixed` abajo, `padding-bottom: env(safe-area-inset-bottom)` para móviles con barra de gestos; el contenido (`.app-main`) recibe un margen inferior igual a la altura de la barra para que nada quede tapado.
- Objetivos táctiles de al menos 44 px y etiquetas de 11 px como mínimo.

## Risks / Trade-offs

- [La vista móvil no se puede comprobar con los tests (jsdom no aplica media queries)] → los tests comprueban el comportamiento (enlaces, panel, contador); la apariencia la revisa la autora en su móvil o en el modo móvil del navegador.
- [Dos navegaciones en el DOM a la vez] → la oculta queda con `display: none`, que también la saca de la navegación por teclado y de los lectores de pantalla.

## Migration Plan

Sin migraciones.

## Open Questions

(ninguna)
