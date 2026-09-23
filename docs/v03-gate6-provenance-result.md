# v0.3 Gate 6 - External Independence / Provenance Result

## Formal role of Gate 6

The v0.3 formal specification defines Gate 6 as:

> External-system integration is blocked until these gates are passed.

The specification does not define a standalone numerical metric or separate scored acceptance procedure for Gate 6.

The acceptance addendum operationalizes the immediate Gate-6 blocker as the availability of genuinely independent authorship/provenance for independent replication.

## Provenance condition

The independent Gate-2 fixture was authored in a separate authoring context.

The resulting artifact consists of:

- `tests/v03/gate2_independent_fixture.json`
- `docs/v03-gate2-independent-author-attestation.md`

The fixture was independently authored before candidate evaluation and accompanied by an author attestation addressing:

- candidate implementation access;
- candidate-specific result access;
- prior holdout/result access;
- fixture freezing;
- absence of candidate-specific tuning.

## Frozen artifact hashes

Independent fixture SHA-256:

`717B2E0D564077B7E65FFA401E337B9376E1CC50F58B5A4C962C77E81A7CDC5B`

Author attestation SHA-256:

`DE4C1713CE9AFE5EC6420FC9F8F8819A4EF3CC68405C870B83E3B1F6A98ED0CC`

## Result

The specific Gate-6 provenance blocker:

```text
genuinely independent authorship/provenance available
```

is now satisfied.

No standalone Gate-6 score is claimed because the frozen specification does not define one.

## Integration status

External-system integration remains blocked.

Reason:

Gate 2 remains open because the fresh independent fixture produced zero paraphrase errors for both frozen v0.2 and frozen v0.3, so material improvement could not be demonstrated under the frozen criterion.

Therefore resolving the Gate-6 provenance blocker does not authorize external-system integration.

## Research boundary

No Gate-6 criterion was changed after evaluation.

No candidate implementation was changed.

No independent fixture was changed.

No historical H5 replication result was relabeled as current Gate-6 evidence.
