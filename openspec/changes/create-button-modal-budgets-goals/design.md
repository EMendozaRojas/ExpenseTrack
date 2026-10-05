## Context

Ver `proposal.md` — Why. Cambio solo de frontend que replica en `/budgets` y `/goals` el patrón ya implementado en `TransactionsPage` (Movimientos): formulario en la página cuando no hay datos y, si los hay, botón en la barra superior + `Modal`.

## Goals / Non-Goals

**Goals:**
- UX coherente entre Movimientos, Presupuestos y Metas.
- Reutilizar componentes y estilos existentes (`Modal`, `.expenses-toolbar`), sin crear piezas nuevas.

**Non-Goals:**
- Editar presupuestos o metas en modal (la edición sigue inline en cada tarjeta).
- Cambios de API o backend.

## Decisions

### D1 — Condición sobre la lista que devuelve `GET /budgets` — DECIDIDO (corregido 2026-10-05)
- La página decide con la lista que devuelve `GET /budgets?year=&month=` para el mes visible: vacía → formulario en la página; con elementos → botón + modal. No hace falta ninguna consulta extra.
- Los presupuestos son **recurrentes** (ver `budgets-and-savings-goals`, D1 ajustado): una fila se evalúa contra cualquier mes, así que la lista es la misma en todos los meses. En la práctica, el formulario en la página solo aparece si el usuario no tiene ningún presupuesto, y cambiar de mes no lo hace reaparecer.
- Corrección: una versión anterior de este documento decía que al ir a un mes sin presupuestos volvía a aparecer el formulario. Esa situación no puede darse con el modelo actual. Si en el futuro los presupuestos pasan a depender del mes (como propone `monthly-budgets-planning`), la misma condición hará que el formulario aparezca en los meses vacíos sin cambiar el código.

### D2 — Un único elemento de formulario reutilizado — DECIDIDO
- El JSX del formulario se define una vez (`budgetForm` / `goalForm`) y se renderiza en la página o dentro del `Modal`, igual que `addMovementForm` en Movimientos. El estado del formulario vive en la página, así que no se duplica lógica.
- El `<h2>` se queda fuera del formulario: en la página lo pone la `<section>` y en el modal lo pone el `title` del `Modal`.

### D3 — Alineación del botón en Metas — DECIDIDO
- Metas no tiene selector de mes, así que la barra `.expenses-toolbar` (`justify-content: space-between`) dejaría el botón a la izquierda. Se añade el modificador `.expenses-toolbar-end` (`justify-content: flex-end`). En móvil se mantiene el comportamiento existente de la barra (columna, botones estirados).

### D4 — Estados de carga y cierre del modal — DECIDIDO
- Durante la carga inicial no se renderiza ni el formulario ni el botón, para evitar un parpadeo del formulario antes de que lleguen los datos.
- `onSuccess` de la mutación de creación cierra el modal; `onError` lo deja abierto con el mensaje de `formError`.

## Risks / Trade-offs

- [Al crear el primer presupuesto desde el formulario en la página, este desaparece y se sustituye por el botón] → es el comportamiento buscado; el nuevo registro aparece en la lista.
