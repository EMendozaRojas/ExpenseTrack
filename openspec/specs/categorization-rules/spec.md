# categorization-rules Specification

## Purpose
Reglas por patrón de texto que asignan automáticamente una categoría a los movimientos según su concepto normalizado, con prioridad configurable, previsualización de impacto y aplicación explícita que nunca pisa una categoría puesta a mano.

## Requirements

### Requirement: User can define categorization rules
The system SHALL allow an authenticated user to create, list, update, enable/disable and delete their own rules (system rules are applied but not listed or editable). Each rule SHALL have a `match_type` of `contains` or `starts_with`, a `pattern`, a target `category_id` visible to the user, and a `priority`. Rules SHALL be isolated per user; system-provided rules SHALL apply to every user at lower priority than any user rule.

#### Scenario: Create a rule
- **WHEN** the user creates a rule mapping the pattern "MERCADONA" (`contains`) to their "Supermercado" category
- **THEN** the system stores the enabled rule owned by that user

#### Scenario: Rule target must be a visible category
- **WHEN** the user creates a rule whose `category_id` does not exist or belongs to another user
- **THEN** the system rejects the request with a "not found" error

#### Scenario: Unsupported match type is rejected
- **WHEN** the user submits a rule with a `match_type` other than `contains` or `starts_with`
- **THEN** the system rejects the request with a validation error

### Requirement: Rules classify uncategorized movements on creation and import
When a transaction is created without a category, or imported, the system SHALL attempt to assign one by evaluating the applicable enabled rules against the normalized text (the counterparty, or the note if there is none, for manual transactions; the statement concept for imported ones), user rules first (`priority` descending, then id) then system rules, applying the first matching rule. Normalization SHALL ignore case, accents, card or account numbers and common bank prefixes. If no rule matches, the transaction SHALL be assigned to "Sin Clasificar".

#### Scenario: Imported movement matched by a rule
- **WHEN** a movement with concept "COMPRA EN MERCADONA 1234" is imported and a rule maps "MERCADONA" to "Supermercado"
- **THEN** the movement is stored with category "Supermercado" (the raw concept still normalizes to a match)

#### Scenario: No rule matches
- **WHEN** an imported movement matches no rule
- **THEN** the movement is stored in "Sin Clasificar" and can be listed by filtering on that category

#### Scenario: Manual category is never overridden by rules
- **WHEN** a transaction already has a category set by the user
- **THEN** rule evaluation does not change its category

### Requirement: User can preview and apply a rule to existing movements
The system SHALL provide a preview that reports how many of the user's non-deleted transactions (of any category) a given pattern would match, and an explicit action to apply a rule, own or system. Applying a rule SHALL only set the category on the user's matching transactions that are currently in "Sin Clasificar"; it SHALL NOT overwrite any other category, whether set by another rule or by hand.

#### Scenario: Preview impact
- **WHEN** the user requests a preview for a pattern
- **THEN** the system returns the count of the user's transactions whose normalized description matches, without modifying anything

#### Scenario: Apply only fills blanks
- **WHEN** the user applies a rule and some matching transactions already have a category other than "Sin Clasificar"
- **THEN** the system sets the rule's category only on the matching transactions in "Sin Clasificar", leaves the rest untouched, and reports how many were updated

### Requirement: User can recategorize movements in bulk
The system SHALL allow the user to assign a single subcategory to a set of their non-deleted transactions in one operation. Unlike rule application, this explicit action SHALL overwrite any existing category on the selected transactions. Afterwards the system SHALL re-evaluate the current month's budget notifications.

#### Scenario: Bulk categorize a selection
- **WHEN** the user submits a list of their transaction ids and a target category visible to them
- **THEN** the system sets that category on all listed transactions they own — replacing any prior category — and reports the count updated

#### Scenario: Bulk categorize ignores ids the user does not own
- **WHEN** the submitted list includes transaction ids owned by another user
- **THEN** the system updates only the caller's transactions and does not reveal the others
