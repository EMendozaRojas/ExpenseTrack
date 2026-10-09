# app-navigation Specification

## Purpose
Navegación de la app en ordenador y en móvil, indicador de notificaciones sin leer y presencia de la marca (mascota y nombre) en las vistas principales.

## Requirements

### Requirement: Desktop navigation is a side menu
On screens wider than 768 px, the app SHALL show a side menu with all sections (Estadísticas, Movimientos, Presupuestos, Metas, Análisis, Notificaciones, Configuración), the user's name and avatar at the top and the brand at the bottom. The current section SHALL be highlighted. The top bar SHALL only contain the «Cerrar sesión» button.

#### Scenario: Unread notifications in the side menu
- **WHEN** the user has 4 unread notifications
- **THEN** the «Notificaciones» item of the side menu shows the number 4

#### Scenario: No duplicated bell
- **WHEN** the user looks at the top bar
- **THEN** there is no notifications bell, only «Cerrar sesión»

### Requirement: Mobile navigation is a bottom bar with a "More" panel
On screens 768 px wide or narrower, the app SHALL show a bar fixed at the bottom with Estadísticas, Movimientos, Presupuestos, Metas and «Más», each with an icon and a readable label, and SHALL NOT show the side menu. «Más» SHALL open a panel with Análisis, Notificaciones and Configuración. The panel SHALL close when the user picks a section, taps outside it or presses Escape. The current section SHALL be highlighted; when it is one of the sections inside «Más», «Más» SHALL be highlighted. Page content SHALL not be hidden behind the bar.

#### Scenario: Open a secondary section
- **WHEN** the user taps «Más» and then «Configuración»
- **THEN** the app opens Configuración and the panel closes

#### Scenario: Close the panel without choosing
- **WHEN** the user opens «Más» and taps outside the panel
- **THEN** the panel closes and the current page does not change

#### Scenario: Unread notifications on "More"
- **WHEN** the user has 4 unread notifications
- **THEN** «Más» shows the number 4, and «Notificaciones» inside the panel also shows 4

### Requirement: The brand mascot appears in every main view
The app SHALL show the same mascot (without letters) next to the name «ExpenseTrack», written as text with «Track» in the accent color, in the desktop side menu, in the mobile top bar and, larger and with the slogan «Tus gastos, siempre contigo», above the login form. The mascot SHALL move with a gentle bounce, and SHALL stay still when the user's system asks for reduced motion. The mascot image SHALL be decorative (empty alternative text) because the name is written next to it.

#### Scenario: Brand on the login page
- **WHEN** a visitor opens the login page
- **THEN** the mascot, the name «ExpenseTrack» and the slogan appear above the form

#### Scenario: Reduced motion
- **WHEN** the user's system has reduced motion enabled
- **THEN** the mascot is shown without the bounce animation
