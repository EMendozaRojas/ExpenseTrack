## ADDED Requirements

### Requirement: Budget cards read top to bottom on mobile
On screens 768 px wide or narrower, each budget card SHALL show, from top to bottom: the category name with its icon; the label «Se repite cada mes» or «Solo este mes»; the amounts as «<spent> de <amount>» with the percentage on the right in the status color; the progress bar; the status text; the spending pace when there is one; and, when the budget is editable, the Editar and Borrar buttons sharing the full width. On wider screens the card SHALL keep its layout (name and label on the left and «<spent> / <amount>» on the right in one row, the bar, the pace, and the status with the percentage next to the buttons).

#### Scenario: Card on a phone
- **WHEN** the user opens Presupuestos on a 390 px wide screen
- **THEN** each card shows the name, the label below it, a row with «340,50 € de 600,00 €» and «56.8%», the bar, «Dentro del presupuesto», the pace and the two buttons side by side at full width, without any text overflowing the card

#### Scenario: Card on a computer
- **WHEN** the user opens Presupuestos on a computer
- **THEN** the card looks as before, with «340,50 € / 600,00 €» next to the name and «Dentro del presupuesto · 56.8%» next to the buttons
