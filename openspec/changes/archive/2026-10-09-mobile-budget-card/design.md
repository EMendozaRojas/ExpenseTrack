## Context

`BudgetCard` pinta: cabecera (nombre + etiqueta | importes «gastado / tope»), barra, ritmo y pie (estado «… · pct%» | Editar, Borrar). Una sola estructura para todas las pantallas.

## Goals / Non-Goals

**Goals:** en el móvil, un dato por línea en el orden de la maqueta; en el ordenador, exactamente el aspecto actual.

**Non-Goals:** cambiar textos, colores, datos o acciones de la tarjeta; tocar otras tarjetas.

## Decisions

### D1 — Un solo marcado, dos órdenes con CSS
- Se mantiene un único componente; el marcado separa cada dato en su elemento (nombre, etiqueta, importe gastado, separador, tope, porcentaje, estado, ritmo, acciones) y el CSS decide su colocación.
- En `≤ 768px`: la cabecera pasa a columna (nombre y etiqueta en líneas distintas; importes y porcentaje en una fila), el pie usa `display: contents` para que estado y acciones se ordenen con `order` junto al ritmo (estado → ritmo → acciones) y las acciones son una rejilla de 2 columnas a todo el ancho.
- Alternativa descartada: detectar el ancho en JavaScript y pintar dos componentes distintos; duplica marcado y añade estado.

### D2 — Textos que cambian entre vistas
- Separador del importe: « / » en el ordenador, « de » en el móvil (dos `span`, uno oculto según la vista).
- Porcentaje: en el ordenador sigue unido al estado («Dentro del presupuesto · 56.8%»); en el móvil se oculta ahí y se muestra a la derecha del importe, con el color del estado. Para lectores de pantalla el porcentaje oculto con `display: none` no se lee dos veces.

## Risks / Trade-offs

- [Dos textos alternativos en el DOM] → los ocultos llevan `display: none`, así que ni se ven ni los leen los lectores de pantalla.

## Migration Plan

Sin migraciones.

## Open Questions

(ninguna)
