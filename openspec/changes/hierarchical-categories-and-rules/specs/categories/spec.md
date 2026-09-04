## Purpose

Taxonomía de ingresos y gastos del usuario: categorías del sistema compartidas y categorías propias, con jerarquía de un nivel y tipo (ingreso o gasto), y reglas de borrado que nunca dejan un movimiento apuntando a una categoría inexistente.

## ADDED Requirements

### Requirement: Categories have a type and an optional parent
The system SHALL give every category a `kind` of `income` or `expense` and an optional `parent_id` referencing a root category of the same `kind`. A subcategory SHALL NOT itself have children (single-level hierarchy). System categories (`owner_id` null) SHALL be visible to every user; a user's own categories SHALL be visible only to that user.

#### Scenario: Create a subcategory
- **WHEN** the user creates a category with a `parent_id` pointing to one of their visible root categories of kind `expense`
- **THEN** the system creates it as a subcategory with the same `kind` as its parent

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
The system SHALL forbid hard-deleting system categories. When a user deletes one of their own categories, the system SHALL reassign its transactions and its subcategories to that category's parent, or to "no category" if it was a root, and SHALL report how many transactions were affected.

#### Scenario: Delete a root category with movements
- **WHEN** the user deletes one of their root categories that has transactions and subcategories
- **THEN** those transactions and subcategories are set to "no category" and the response reports the affected transaction count

#### Scenario: Attempt to delete a system category
- **WHEN** the user attempts to delete a system category
- **THEN** the system rejects the request and the category remains
