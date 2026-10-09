## 1. Imagen de la mascota

- [x] 1.1 Generar `frontend/public/mascota.png` (600×400) a partir de `Design System/logo sin fondo listo.png` y versionar los dos archivos

## 2. Marca

- [x] 2.1 `components/BrandMark.tsx` con las variantes `sidebar`, `topbar` y `hero` (mascota + «Expense**Track**», lema en `hero`); estilos y animación `mascot-bounce` con `prefers-reduced-motion`
- [x] 2.2 Menú lateral: sustituir `/logo.png` por `BrandMark` (`sidebar`)
- [x] 2.3 `LoginPage`: `BrandMark` (`hero`) encima del formulario

## 3. Navegación

- [x] 3.1 `NAV_ITEMS` con el campo `mobile` (`bar` / `more`)
- [x] 3.2 Quitar la campanita de la barra superior; en el móvil, `BrandMark` (`topbar`) a la izquierda
- [x] 3.3 `components/MobileNav.tsx`: barra inferior con las 4 secciones y «Más» con contador; panel «Más» (se cierra al elegir, al tocar fuera y con Escape; «Más» activo en secciones secundarias)
- [x] 3.4 CSS: en `≤ 768px` ocultar el menú lateral y mostrar `MobileNav` (fija abajo, área segura, margen inferior del contenido); en `> 768px` ocultar `MobileNav`; eliminar los estilos de la fila horizontal anterior

## 4. Tests

- [x] 4.1 `AppLayout`: sin campanita en la barra superior; contador en el menú lateral; mascota presente
- [x] 4.2 `MobileNav`: 4 secciones + «Más»; abrir «Más» muestra las 3 secundarias con el contador; elegir una cierra el panel y navega; Escape y tocar fuera lo cierran; «Más» activo en una ruta secundaria
- [x] 4.3 `LoginPage`: muestra el nombre y el lema

## 5. Verificación

- [x] 5.1 `tsc`, `eslint` y `vitest` en verde; Prettier sin avisos en los archivos tocados
- [x] 5.2 Revisión visual en el ordenador (navegador) y en vista móvil por la autora
