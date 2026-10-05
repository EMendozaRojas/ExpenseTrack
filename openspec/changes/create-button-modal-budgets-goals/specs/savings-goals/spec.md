## ADDED Requirements

### Requirement: Goal creation UI adapts to whether the user has goals
The goals page SHALL show the "Nueva meta de ahorro" form inline when the user has no savings goals. When the user has at least one goal, the page SHALL hide the inline form and SHALL show a "+ Nueva meta" button aligned to the top-right of the page that opens the same form in a modal dialog. While goals are loading, the page SHALL show neither the inline form nor the button.

#### Scenario: No goals shows the inline form
- **WHEN** the user with no savings goals opens the goals page
- **THEN** the creation form is visible on the page and no "+ Nueva meta" button is shown

#### Scenario: Existing goals show the button instead of the form
- **WHEN** the user with at least one goal opens the goals page
- **THEN** the inline form is hidden and the "+ Nueva meta" button is shown in the top-right

#### Scenario: Button opens the form in a modal
- **WHEN** the user clicks "+ Nueva meta"
- **THEN** a dialog titled "Nueva meta de ahorro" opens containing the creation form

#### Scenario: Modal closes after a successful creation
- **WHEN** the user submits a valid goal from the modal and the API accepts it
- **THEN** the modal closes and the list refreshes with the new goal

#### Scenario: Modal stays open on error
- **WHEN** the API rejects the goal created from the modal
- **THEN** the modal stays open and shows the error message
