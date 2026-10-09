## Why

En el móvil, la tarjeta de cada presupuesto mete en una sola fila el nombre, la etiqueta «Se repite cada mes» y los importes, que se parten en dos líneas; abajo, el estado con el porcentaje queda encajonado contra los botones Editar y Borrar. La información está, pero cuesta leerla. Maqueta aprobada por la autora el 2026-10-09 (artefacto «Menú móvil: dos opciones», fila «Presupuestos en el móvil · la tarjeta»).

## What Changes

Solo en pantallas de 768 px o menos (en el ordenador la tarjeta no cambia):

1. Nombre arriba, más grande, con la etiqueta («Se repite cada mes» / «Solo este mes») debajo.
2. Importes en su propia fila: «340,50 € de 600,00 €», con el porcentaje a la derecha en el color del estado.
3. La barra de progreso.
4. El estado («Dentro del presupuesto», «Cerca del límite», «Superado») y, debajo, el ritmo de gasto.
5. Editar y Borrar ocupando todo el ancho, mitad y mitad.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `budgets`: la tarjeta de cada presupuesto se reorganiza en el móvil para leerse de arriba abajo.

## Impact

- **Frontend**: `features/budgets/components/BudgetCard.tsx` (marcado con los datos separados para poder ordenarlos), `index.css` (estilos de la tarjeta en `≤ 768px`), test de la tarjeta.
- **Backend**: sin cambios.
