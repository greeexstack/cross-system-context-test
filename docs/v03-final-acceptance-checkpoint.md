# v0.3 Final Acceptance Checkpoint

## Current Repository State

HEAD:

`checkpoint commit for this document`

Working tree is expected to remain clean after this checkpoint.

## Acceptance State

| Gate | Status | Evidence |
|---|---|---|
| Gate 1 | CLOSED | Frozen v0.2 regression suite passes |
| Gate 2 | NOT DEMONSTRATED | Independent fixture: v0.2 = 0 errors, v0.3 = 0 errors; relative improvement cannot be demonstrated from a zero-error baseline |
| Gate 3 | PASS | Canonical MR4-MR9 unsupported change rate = 0.0%; independent different-work-item controls preserved |
| Gate 4 | CLOSED | Correctness measurement remains separated from reasoner semantic control |
| Gate 5 | CLOSED | Measurement/reporting deterministic |
| Gate 6 | PROVENANCE CONDITION SATISFIED | Independent authorship/provenance requirement satisfied; external-system integration remains blocked while Gate 2 is not demonstrated |

## Frozen Artifacts

v0.2 baseline:

`v0.2.0` / `60f125a09ffa417cdc91c1dc2c40a1dc0a17466a`

Frozen v0.3 candidate:

`05f8cbf`

Independent Gate-2 fixture SHA-256:

`717B2E0D564077B7E65FFA401E337B9376E1CC50F58B5A4C962C77E81A7CDC5B`

Independent Gate-2 attestation SHA-256:

`DE4C1713CE9AFE5EC6420FC9F8F8819A4EF3CC68405C870B83E3B1F6A98ED0CC`

## Final Gate-2 Measurement

Independent fixture:

- 5 cases
- 15 paraphrase pairs
- v0.2 errors: 0
- v0.3 errors: 0
- v0.2 fidelity: 1.0
- v0.3 fidelity: 1.0
- Gate 2 verdict: NOT DEMONSTRATED

Post-evaluation extractor coverage diagnostic:

- development texts: 20/20 with frames
- development total frames: 28
- independent texts: 0/20 with frames
- independent total frames: 0
- development coverage: 100.0%
- independent coverage: 0.0%

## Interpretation Boundary

The current evidence supports:

> 100% tested-domain extraction accuracy; 0% demonstrated independent-fixture coverage.

The Gate-2 result is not reclassified because the independent fixture remains frozen and the acceptance criterion remains frozen.

No candidate tuning, fixture modification, acceptance-criterion modification, or new H-series experiment was performed in response to the Gate-2 result.

## Next Research Boundary

v0.3 acceptance work is complete for the current frozen candidate.

Any attempt to improve independent semantic coverage must begin as a new research hypothesis and a new controlled experiment. It must not modify the frozen v0.3 candidate or retroactively alter the completed Gate-2 evaluation.



