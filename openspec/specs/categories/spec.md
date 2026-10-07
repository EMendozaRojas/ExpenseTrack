# categories Specification

## Purpose
Taxonomía de ingresos y gastos del usuario: categorías del sistema compartidas y categorías propias, con jerarquía de un nivel y tipo (ingreso o gasto), y reglas de borrado que nunca dejan un movimiento apuntando a una categoría inexistente.

## Requirements

### Requirement: Categories have a type and an optional parent
The system SHALL give every category a `kind` of `income` or `expense` and an optional `parent_id` referencing a root category of the same `kind`. A subcategory SHALL NOT itself have children (single-level hierarchy). System categories (`owner_id` null) SHALL be visible to every user; a user's own categories SHALL be visible only to that user. A category MAY have an icon, a color and an `is_fixed` flag marking fixed expenses (rent, subscriptions…). Transactions SHALL always be assigned to a subcategory, never to a root category; a transaction without an explicit category is assigned to the system subcategory "Sin Clasificar" of its kind.

#### Scenario: Create a subcategory
- **WHEN** the user creates a category with a `parent_id` pointing to one of their visible root categories of kind `expense`
- **THEN** the system creates it as a subcategory with the same `kind` as its parent

#### Scenario: Transactions cannot use a root category
- **WHEN** the user records or edits a transaction with a root category
- **THEN** the system rejects the request with a validation error

#### Scenario: Reject a second-level subcategory
- **WHEN** the user creates a category whose `parent_id` points to a category that already has a parent
- **THEN** the system rejects the request with a validation error

#### Scenario: List as a tree filtered by kind
- **WHEN** the user requests categories for `kind=expense`
- **THEN** the system returns that user's own plus all system expense categories, grouped as roots with their subcategories, ordered by name

### Requirement: Category names are unique within their scope
The system SHALL enforce that a category name is unique for a given `(owner, parent, kind)`. System categories SHALL be unique by `(name, kind)` among categories with no owner.

#### Scenario: Duplicate name under the same parent
- **WHEN** the user creates a category with a name that already exists under the same parent and kind for that user
- **THEN** the system rejects the request with a conflict error

### Requirement: Default system categories are seeded
The system SHALL provide a predefined set of system categories (with subcategories) for both `income` and `expense`, available to every user without the user creating them.

#### Scenario: New user sees system categories
- **WHEN** a freshly registered user lists their categories
- **THEN** the system returns the predefined system categories for income and expense

### Requirement: Deleting a category never orphans movements
The system SHALL forbid deleting system categories. When a user deletes one of their own categories, the system SHALL move its subcategories up to the deleted category's parent (they become roots if it was a root), SHALL reassign its transactions to "Sin Clasificar" of the same kind, and SHALL report how many transactions and subcategories were reassigned.

#### Scenario: Delete a root category with movements
- **WHEN** the user deletes one of their root categories that has transactions and subcategories
- **THEN** its transactions move to "Sin Clasificar", its subcategories become roots, and the response reports both counts

#### Scenario: Attempt to delete a system category
- **WHEN** the user attempts to delete a system category
- **THEN** the system rejects the request and the category remains
