# Cross-System Context Reasoning & Robustness Experiment — v0.2 Fixtures

Frozen fixture package for v0.2.

**Experiment timestamp:** `2026-09-13T12:00:00Z` (fixture timestamps are UTC).
**Method:** controlled paired/metamorphic scenarios.
**v0.1 status:** untouched and out of scope.

## Frozen hypothesis
When a secondary business data source contains context that is materially relevant to a primary-system situation, a cross-system reasoning engine should correctly modify, strengthen, weaken, or preserve the primary interpretation according to the secondary evidence. It should reject context that is unrelated, incorrectly attributed, temporally inappropriate, or insufficiently certain.

## Evaluation dimensions
`context_sensitivity`, `context_resistance`, `direction_correctness`, `evidence_validity`, `identity_integrity`, `temporal_integrity`, `ambiguity_handling`, `missing_data_handling`, `generalization`.

## Fixture structure
- `fixtures/customers.json`: authoritative customer identities used for matching.
- `fixtures/opportunities.json`: primary opportunity/service workflow records.
- `fixtures/quotes.json`: quote state for quote workflows.
- `fixtures/communications.json`: secondary communication observations.
- `fixtures/scenario_pairs.json`: 20 frozen paired/metamorphic cases: one development and one evaluation case for each F01–F10.
- `ground_truth/development.json`: expected assertions for development cases.
- `ground_truth/evaluation.json`: sealed evaluation assertions for evaluation cases.
- `validate_fixtures.py`: deterministic invariant/schema validator.

## Non-goals / prohibited reasoning
The fixtures do **not** assert causal or root-cause relationships. Secondary-data existence is never evidence by itself. No scenario permits stronger conclusions than the supplied observations support. Wrong-customer and ambiguous identities are deliberately blocked. Clearly stale context is not current context.

## Important frozen corrections
- F02 strengthens the same interpretation class; it must not become a class change.
- F05 is definite `no_match`: different name, email, and phone.
- F06 is `ambiguous_match`: same name, no email/phone.
- F07 changes timestamp only; identity and content remain constant.
- F08 distinguishes source unavailable from available/no communication.
- F09 explicitly reverts toward primary-only after context removal.
- F10 is a service completion / next-step workflow, not another quote scenario.

## Validation
From the package directory:

```bash
python validate_fixtures.py
```
Expected result: `VALIDATION PASS` with all invariant groups passing.
