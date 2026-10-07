## ADDED Requirements

### Requirement: System suggests goals from reference financial frameworks
On `GET /goals/suggestions`, the system SHALL return two goal presets computed from the user's own data:
- **Fondo de emergencia**: `target_amount = 6 × average monthly expense` over the three complete calendar months before the current one. The response SHALL also include the current months of coverage (`liquid assets / average monthly expense`, where liquid assets is the sum of balances of the user's non-archived accounts of type `general`, `cash`, `checking` or `wallet`) and its band: `critical` (< 1), `minimum` (1–3), `adequate` (3–6), `strong` (6–12) or `exceptional` (≥ 12).
- **Independencia financiera**: `target_amount = 25 × annual expense`, where annual expense is the user's total expense over the twelve complete calendar months before the current one.

Each preset SHALL include the values used in the calculation. When the user has no expenses in the relevant window, the preset SHALL be returned without a `target_amount` and flagged as not enough data. Presets are suggestions only: creating a goal SHALL NOT require or validate against them.

#### Scenario: Emergency fund preset
- **WHEN** the user's average monthly expense over the last three complete months is 1500.00
- **THEN** the "Fondo de emergencia" preset suggests a target of 9000.00 with the 1500.00 average as its basis

#### Scenario: Coverage band
- **WHEN** the user's liquid assets are 4000.00 and their average monthly expense is 1000.00
- **THEN** the emergency fund preset reports 4.0 months of coverage in the `adequate` band

#### Scenario: Not enough data
- **WHEN** the user has no expenses in the last three complete months
- **THEN** the emergency fund preset has no target amount and is flagged as not enough data

#### Scenario: Creating a goal from a preset
- **WHEN** the user picks a preset in the create-goal form
- **THEN** the form is prefilled with the preset's name and target amount, and the user can edit both before creating
