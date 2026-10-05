## ADDED Requirements

### Requirement: Budget creation UI adapts to whether the user has budgets
The budgets page SHALL show the "Nuevo presupuesto" form inline when the list of budgets returned for the visible month is empty. When that list has at least one budget, the page SHALL hide the inline form and SHALL show a "+ Nuevo presupuesto" button in the top toolbar, to the right of the month navigator, that opens the same form in a modal dialog. Because budgets are recurring and the list is the same for every month, in practice the inline form SHALL appear only when the user has no budgets at all. While budgets are loading, the page SHALL show neither the inline form nor the button.

#### Scenario: No budgets shows the inline form
- **WHEN** the user with no budgets opens the budgets page
- **THEN** the creation form is visible on the page and no "+ Nuevo presupuesto" button is shown

#### Scenario: Existing budgets show the button instead of the form
- **WHEN** the user with at least one budget opens the budgets page
- **THEN** the inline form is hidden and the "+ Nuevo presupuesto" button is shown in the top-right of the toolbar

#### Scenario: Changing month keeps the button
- **WHEN** the user with at least one budget moves to another month
- **THEN** the button is still shown and the inline form stays hidden

#### Scenario: Button opens the form in a modal
- **WHEN** the user clicks "+ Nuevo presupuesto"
- **THEN** a dialog titled "Nuevo presupuesto" opens containing the creation form

#### Scenario: Modal closes after a successful creation
- **WHEN** the user submits a valid budget from the modal and the API accepts it
- **THEN** the modal closes and the list refreshes with the new budget

#### Scenario: Modal stays open on error
- **WHEN** the API rejects the budget created from the modal
- **THEN** the modal stays open and shows the error message
