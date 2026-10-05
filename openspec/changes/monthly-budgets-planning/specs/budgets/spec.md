## MODIFIED Requirements

### Requirement: User can set a monthly spending cap on any expense category
The system SHALL allow an authenticated user to create a budget for one of their visible expense categories (root or subcategory) in a given month, with an `amount` greater than zero and a `repeat` option that defaults to on. With `repeat` on, the same amount SHALL apply to that month and every following month until the user changes or deletes it. With `repeat` off, the budget SHALL apply only to that month. A category SHALL have at most one budget in any given month. The user SHALL be able to create budgets for the current month and for future months, but not for past months. Budgets SHALL be isolated per user. Budget amounts SHALL be expressed in the user's single currency.

#### Scenario: Create a budget on a root category
- **WHEN** in October the user creates a 300.00 budget for their "Alimentación" root category in October with `repeat` on
- **THEN** "Alimentación" has a 300.00 budget owned by that user in October, November and every later month

#### Scenario: Create a budget on a subcategory
- **WHEN** the user creates a budget for their "Suscripciones" subcategory
- **THEN** the system stores it, independent of any budget on that subcategory's parent

#### Scenario: Create a one-month budget
- **WHEN** the user creates a 150.00 budget for "Ocio" in October with `repeat` off
- **THEN** "Ocio" has a budget in October and none in November

#### Scenario: Budget does not apply before it was created
- **WHEN** the user lists budgets for September after creating a repeating budget in October
- **THEN** that budget is not included in September

#### Scenario: Plan a future month
- **WHEN** in October the user creates a 600.00 budget for "Regalos" in December with `repeat` off
- **THEN** "Regalos" has a budget only in December

#### Scenario: Duplicate budget
- **WHEN** the user creates a budget for a category that already has a budget in that month
- **THEN** the system rejects the request with a conflict error

#### Scenario: Budget on a non-expense or foreign category
- **WHEN** the user targets an income category, or a category not visible to them
- **THEN** the system rejects the request with a "not found" error

#### Scenario: Non-positive amount
- **WHEN** the user sends an `amount` of zero or less
- **THEN** the system rejects the request with a validation error

#### Scenario: Root and subcategory budgets coexist
- **WHEN** the user has a budget on "Alimentación" and another on its subcategory "Restaurantes" in the same month
- **THEN** both are evaluated independently, and no response adds their amounts together

### Requirement: Budget status reflects spending against the cap
`GET /budgets?year=&month=` SHALL return one entry per category with a budget in that month, with `category_id`, `category_name`, `amount` for that month, `repeats`, `editable` (true only for the current and future months), `spent`, `pct = spent / amount × 100` (rounded to one decimal, may exceed 100), a `status` of `ok` (`pct` below 80), `warning` (`pct` from 80 to under 100) or `exceeded` (`pct` 100 or more), and `pace`. `spent` SHALL include only expenses dated in that month, aggregating the category subtree for root categories, and SHALL be computed from the current transactions, so corrections to past transactions are reflected in past months. Spending or savings from one month SHALL NOT affect another.

#### Scenario: Spending crosses into warning
- **WHEN** the user's `spent` in a budgeted category reaches 80% of that month's amount
- **THEN** that budget's status for the month is `warning`

#### Scenario: Spending exceeds the cap
- **WHEN** the user's `spent` reaches 100% or more of that month's amount
- **THEN** that budget's status for the month is `exceeded`

#### Scenario: Each month starts at zero
- **WHEN** a repeating 300.00 budget had 250.00 spent in September and nothing yet in October
- **THEN** October shows `spent` 0.00 against 300.00, with nothing carried over

#### Scenario: Late correction updates a past month
- **WHEN** the user imports a September expense in October
- **THEN** September's `spent` for that budget includes it, while September's amount stays unchanged

### Requirement: Threshold crossings raise notifications
The system SHALL evaluate the budgets that apply to the current month and, for each category, when `pct` is 100 or more SHALL create a `budget_exceeded` notification, or else when `pct` is 80 or more, a `budget_warning` notification. No other thresholds SHALL produce budget notifications, and budgets of past months SHALL NOT produce notifications. The same `(category, type, month)` SHALL NOT produce more than one notification, even if the amount changes during the month. The evaluation SHALL run after the user creates, updates, deletes or restores a transaction, bulk-recategorizes transactions, commits a statement import, creates, updates or deletes a budget, or copies budgets from the previous month. It SHALL also run each time the user accesses the application, through `POST /notifications/check`, which the frontend SHALL call once per authenticated app load. When email delivery is configured, the system SHALL also send the notification by email.

#### Scenario: Warning notification once per month
- **WHEN** an expense pushes a budget past 80% and later another expense keeps it between 80% and 100% in the same month
- **THEN** exactly one `budget_warning` notification exists for that category and month

#### Scenario: Notification after a bulk import
- **WHEN** a committed import pushes a budgeted category past 80% for the current month
- **THEN** a `budget_warning` notification for that category and month is created as part of the import commit

#### Scenario: Notification after restoring a transaction
- **WHEN** the user restores a deleted expense and it pushes a budget to 100%
- **THEN** a `budget_exceeded` notification is created for that category and month

#### Scenario: Exceeded notification
- **WHEN** an expense pushes a budget to 100% or more in the current month
- **THEN** a `budget_exceeded` notification is created for that category and month

#### Scenario: Lowering the amount triggers a notification
- **WHEN** the user lowers this month's amount so that current spending is now at 80% or more
- **THEN** the corresponding notification is created

#### Scenario: Missed notification is created when accessing the app
- **WHEN** the user opens the app and a budget is over a threshold for the current month with no corresponding notification
- **THEN** the missing notification is created, and none is duplicated for thresholds already notified

#### Scenario: Past months never notify
- **WHEN** a late import pushes a September budget past 100% in October
- **THEN** no notification is created, and September shows the budget as `exceeded`

### Requirement: Budget creation UI adapts to whether the user has budgets
The budgets page SHALL show the "Nuevo presupuesto" form inline when the visible month is the current or a future month and the list of budgets returned for that month is empty. When that list has at least one budget, the page SHALL hide the inline form and SHALL show a "+ Nuevo presupuesto" button in the top toolbar, to the right of the month navigator, that opens the same form in a modal dialog. Because budgets are defined per month, the inline form SHALL appear in any current or future month without budgets, even if other months have them. In past months, which are read-only, the page SHALL show neither the inline form nor the button. While budgets are loading, the page SHALL show neither the inline form nor the button.

#### Scenario: No budgets shows the inline form
- **WHEN** the user opens the budgets page on the current month and it has no budgets
- **THEN** the creation form is visible on the page and no "+ Nuevo presupuesto" button is shown

#### Scenario: Existing budgets show the button instead of the form
- **WHEN** the user opens the budgets page on a month with at least one budget
- **THEN** the inline form is hidden and the "+ Nuevo presupuesto" button is shown in the top-right of the toolbar

#### Scenario: Changing month keeps the button
- **WHEN** the user moves from a month with budgets to another current or future month that also has budgets
- **THEN** the button is still shown and the inline form stays hidden

#### Scenario: Future month without budgets shows the inline form
- **WHEN** the user moves to a future month that has no budgets, while other months have them
- **THEN** the creation form is visible on the page for that month and no button is shown

#### Scenario: Past months offer no creation
- **WHEN** the user moves to a past month, with or without budgets
- **THEN** neither the inline form nor the "+ Nuevo presupuesto" button is shown

#### Scenario: Button opens the form in a modal
- **WHEN** the user clicks "+ Nuevo presupuesto"
- **THEN** a dialog titled "Nuevo presupuesto" opens containing the creation form

#### Scenario: Modal closes after a successful creation
- **WHEN** the user submits a valid budget from the modal and the API accepts it
- **THEN** the modal closes and the list refreshes with the new budget

#### Scenario: Modal stays open on error
- **WHEN** the API rejects the budget created from the modal
- **THEN** the modal stays open and shows the error message

## ADDED Requirements

### Requirement: Editing and deleting a repeating budget asks for the scope
For a budget in the current or a future month, the user SHALL be able to change its amount or delete it. When the budget repeats, the user SHALL choose a scope: `this` (only that month) or `following` (that month and every later month). Editing with `following` SHALL keep any later month whose amount was set individually; deleting with `following` SHALL remove the budget from that month onwards, including individually set later months. Before confirming, the system SHALL let the frontend list the individually set later months affected (`GET /budgets/{category_id}/planned?from=`). The user SHALL also be able to turn `repeat` on for a one-month budget (it repeats from that month) or off for a repeating one (it stops after that month). Changes SHALL never alter months before the edited month.

#### Scenario: Change only this month
- **WHEN** "Alimentación" repeats at 200.00 and the user sets December to 400.00 with scope `this`
- **THEN** December is 400.00 and January is 200.00

#### Scenario: Change this month and the following ones
- **WHEN** "Alimentación" repeats at 200.00 and the user sets November to 300.00 with scope `following`
- **THEN** November and later months are 300.00, and October stays 200.00

#### Scenario: Individually planned months are kept when editing
- **WHEN** December was set individually to 600.00 and the user changes November to 300.00 with scope `following`
- **THEN** December stays 600.00, January is 300.00, and the confirmation mentioned December

#### Scenario: Delete only this month
- **WHEN** the user deletes November of a repeating budget with scope `this`
- **THEN** November has no budget for that category and December still has it

#### Scenario: Delete this month and the following ones
- **WHEN** the user deletes November of a repeating budget with scope `following`
- **THEN** the category has no budget from November onwards, including individually planned months, and October keeps its budget

#### Scenario: Stop repeating
- **WHEN** the user turns `repeat` off on a repeating budget in November
- **THEN** November keeps its budget and December has none

### Requirement: Past months are read-only
The system SHALL reject with a conflict error any creation, edit, deletion or copy targeting a month before the current month. Past months SHALL keep showing their amounts as they were.

#### Scenario: Editing a past month
- **WHEN** in October the user tries to change September's amount
- **THEN** the system rejects the request with a conflict error

#### Scenario: Later changes do not rewrite history
- **WHEN** in December the user changes a repeating 200.00 budget to 400.00 with scope `following`
- **THEN** October and November still show 200.00

### Requirement: Spending pace projects the end of the current month
For the current month, each budget SHALL include `pace` with `projected = spent / elapsed days × days in month` (elapsed days including today) and `will_exceed = projected >= amount`. `pace` SHALL be null for other months and during the first five days of the month. Pace SHALL NOT produce notifications.

#### Scenario: Pace warns visually before the threshold
- **WHEN** on day 10 of a 30-day month a 300.00 budget has 150.00 spent
- **THEN** `pace.projected` is 450.00 and `pace.will_exceed` is true, and no notification is created

#### Scenario: Too early in the month
- **WHEN** it is day 3 of the month
- **THEN** `pace` is null

### Requirement: Month-close summary notification
When the user accesses the application in a month whose previous month had at least one budget, and no summary exists for that previous month, the system SHALL create a `budget_month_summary` notification stating how many of that month's budgets were kept (`pct` below 100) out of the total, and listing the exceeded ones with their `pct`. Only the immediately previous month SHALL be summarized.

#### Scenario: Summary on first access of the month
- **WHEN** the user opens the app on 2 October and September had 6 budgets, 2 of them exceeded
- **THEN** a summary notification says 4 of 6 budgets were kept and lists the 2 exceeded ones

#### Scenario: Summary only once
- **WHEN** the user opens the app again in October
- **THEN** no second September summary is created

### Requirement: User can copy one-month budgets from the previous month
For the current or a future month, the system SHALL offer the previous month's one-month (non-repeating) budgets whose category has no budget in the target month (`GET /budgets/copy-preview`). The user SHALL be able to select which to copy and adjust their amounts; `POST /budgets/copy` SHALL create them as one-month budgets in the target month and SHALL skip, without overwriting, any category that already has a budget there.

#### Scenario: Copy with adjustments
- **WHEN** October has one-month budgets "Ocio" 150.00 and "Ropa" 100.00 and in November the user copies both, changing "Ropa" to 200.00
- **THEN** November has "Ocio" 150.00 and "Ropa" 200.00, both one-month

#### Scenario: Repeating budgets are not offered
- **WHEN** October has a repeating budget for "Alimentación"
- **THEN** the copy preview for November does not include it

#### Scenario: Never overwrites
- **WHEN** a copied category already has a budget in the target month
- **THEN** that item is skipped and reported, and the existing budget is unchanged

### Requirement: Deleting a category keeps its budget history
When the user deletes a category that has budgets, the system SHALL keep that category's budgets in past months with the category name, amount and the spending they had at the moment of deletion, SHALL remove its budgets from the current month onwards, and SHALL create a `budget_category_deleted` notification telling the user.

#### Scenario: History survives category deletion
- **WHEN** "Gimnasio" had a 40.00 budget with 35.00 spent in September and the user deletes the category in October
- **THEN** September still shows "Gimnasio" 40.00 with 35.00 spent, October and later have no "Gimnasio" budget, and the user is notified

### Requirement: System recommends budget amounts from history
On `GET /budgets/recommendations` (optionally filtered by `category_id`), for each of the user's expense categories with enough recent history, the system SHALL return a suggested monthly amount and a flag of `raise`, `lower`, `keep` or `create`, with a `basis` containing the three monthly spend values, their mean and the spending in the same month of the previous year (or null). The window SHALL be the three complete calendar months before the current one, aggregating the subtree for root categories; a category SHALL be considered only if at least two of those months had spending, and the suggestion SHALL be the rounded mean of the months that had spending. Against the category's budget for the current month, the flag SHALL be `keep` when the suggestion is within 10% of its amount, otherwise `raise` or `lower`; with no budget and spending in all three months, `create`. The same-month-last-year value and, for system root categories, `share_pct` and `over_typical` SHALL be informative and SHALL NOT change the suggestion or the flag. Recommendations SHALL be shown in the create/edit budget form for the chosen category and in a separate view.

#### Scenario: Adjust an existing budget
- **WHEN** a budgeted category's recent mean spend is more than 10% above its current amount
- **THEN** the response flags it `raise`, with the suggested amount and its basis

#### Scenario: Keep a well-sized budget
- **WHEN** a budgeted category's recent mean spend is within 10% of its current amount
- **THEN** the response flags it `keep`

#### Scenario: Suggest a new budget
- **WHEN** an unbudgeted category had spending in each of the last three complete months
- **THEN** the response includes a `create` recommendation with the suggested amount

#### Scenario: Seasonal reference
- **WHEN** the category had spending in the same month last year
- **THEN** the basis includes that value, and the suggested amount is still the three-month mean

#### Scenario: Insufficient history
- **WHEN** a category had spending in only one of the last three complete months
- **THEN** no recommendation is returned for it
