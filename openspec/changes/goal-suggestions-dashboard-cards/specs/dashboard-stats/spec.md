## ADDED Requirements

### Requirement: Dashboard shows budget and goal cards
The dashboard SHALL show a budgets card listing the user's budgets in `warning` or `exceeded` status for the selected month, each with its category, `spent`, `amount` and `pct`, and a link to the budgets page. When no budget is in warning or exceeded status, the card SHALL say all budgets are on track; when the user has no budgets, the card SHALL invite them to create one. The dashboard SHALL also show a goals card listing the user's `active` goals with their progress (`current_amount`, `target_amount`, `pct`) and a link to the goals page; when the user has no active goals, the card SHALL invite them to create one.

#### Scenario: Budgets at risk on the dashboard
- **WHEN** the user has one budget in `exceeded` and one in `ok` for the selected month
- **THEN** the budgets card shows only the exceeded budget

#### Scenario: All budgets on track
- **WHEN** all of the user's budgets are `ok` for the selected month
- **THEN** the budgets card says all budgets are on track

#### Scenario: Active goals progress
- **WHEN** the user has two active goals and one completed goal
- **THEN** the goals card shows the two active goals with their progress
