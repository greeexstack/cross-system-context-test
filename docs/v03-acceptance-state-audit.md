# v0.3 Acceptance State Audit

## Purpose

This document consolidates the acceptance evidence currently established for the v0.3 experiment.

It does not introduce, modify, or retroactively reinterpret any acceptance criterion.

The authoritative acceptance rules remain those fixed in:

`docs/v03-acceptance-gates-addendum.md`

The v0.3 formal specification remains:

`docs/v03-formal-specification.md`

---

# 1. Executive status

| Gate                                        | Status                         | Evidence state                                                                                         |
| ------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------ |
| Gate 1 — Frozen v0.2 regression             | CLOSED                         | Frozen v0.2 suite passed 20/20                                                                         |
| Gate 2 — Paraphrase robustness              | NOT DEMONSTRATED               | Fresh independent fixture produced 0 errors for both v0.2 and v0.3                                     |
| Gate 3 — Resistance                         | PASS                           | Canonical MR4–MR9 unsupported-change rate = 0.0; independent negative controls = 0 unsupported changes |
| Gate 4 — Non-circularity                    | CLOSED                         | Reasoner isolation and evaluator-side truth separation established                                     |
| Gate 5 — Reproducibility                    | CLOSED                         | Repeated measurement and determinism checks passed                                                     |
| Gate 6 — External independence / provenance | PROVENANCE CONDITION SATISFIED | Independent authorship/provenance obtained; external integration remains blocked                       |

Overall v0.3 acceptance status:

```text
NOT COMPLETE
```

The unresolved acceptance issue is Gate 2.

---

# 2. Gate 1 — Frozen v0.2 regression

## Status

**CLOSED**

The frozen v0.2 baseline is identified by:

`v0.2.0`

The frozen v0.2 test suite:

`tests/test_v02.py`

established:

```text
20 / 20 cases passed
```

The v0.2 source under:

`src/experiment/v02`

was unchanged relative to the frozen v0.2 reference used for the acceptance check.

Gate 1 therefore remains closed.

---

# 3. Gate 2 — Paraphrase robustness

## Status

**NOT DEMONSTRATED**

### Frozen protocol

The Gate-2 decision tuple is:

```text
interpretation_class
support_level
decision_strength
recommended_focus
```

Let:

```text
E2 = v0.2 paraphrase errors
E3 = v0.3 paraphrase errors
```

The frozen improvement rule is:

```text
E3 <= floor(E2 / 2)
```

When:

```text
E2 = 0
```

the protocol explicitly classifies the result as:

```text
Gate 2: not demonstrated
```

rather than allowing an equally perfect v0.3 result to count as material improvement.

### Fresh independent evaluation

Independent fixture:

`tests/v03/gate2_independent_fixture.json`

Population:

```text
5 cases
15 canonical-to-paraphrase pairs
```

Observed result:

```text
v0.2:
15 / 15 faithful
0 errors
1.0 fidelity

v0.3:
15 / 15 faithful
0 errors
1.0 fidelity
```

Recorded result:

`docs/v03-gate2-independent-result.json`

The frozen protocol therefore produces:

```text
E2 = 0
E3 = 0
```

and the formal result:

```text
Gate 2: NOT DEMONSTRATED
```

### Interpretation

The result does not establish a measurable material improvement of v0.3 over frozen v0.2 on this fresh fixture.

The result also does not justify changing:

* the error-reduction threshold;
* the decision tuple;
* the fixture;
* the candidate;
* the semantic oracle.

Those artifacts remain frozen.

### Diagnostic observation

Both systems produced perfect pairwise preservation on the independent fixture.

The resulting behavior was predominantly primary-state preservation rather than rich secondary-evidence-driven transitions.

This observation is diagnostic only. It must not be used to alter the frozen Gate-2 acceptance experiment.

---

# 4. Gate 3 — Resistance

## Status

**PASS**

The frozen canonical resistance population is the MR4–MR9 population:

```text
MR4 — irrelevant evidence
MR5 — wrong identity
MR6 — ambiguous identity
MR7 — stale evidence
MR8 — unavailable source
MR9 — no secondary evidence / evidence removal
```

Canonical result:

```text
9 total cases
9 directionally correct
Unsupported Change Rate = 0.0
```

The Gate-3 tolerance is zero unsupported changes.

### Independent negative control

The independent different-work-item family was also evaluated under the Gate-3 material-change definition.

Result:

```text
3 trials
0 unsupported changes
Unsupported Change Rate = 0.0
3 / 3 preserved
```

### Candidate freeze

The frozen v0.3 candidate is:

`ClauseLocalRelationalEventFrameExtractor`

Frozen at:

`05f8cbf`

The candidate files were verified unchanged relative to that freeze.

Recorded result:

`docs/v03-gate3-result.md`

Gate 3 therefore satisfies its frozen acceptance rule.

---

# 5. Gate 4 — Non-circularity

## Status

**CLOSED**

The v0.3 reasoner does not receive experiment ground truth as semantic input.

The accepted separation is:

```text
reasoner
    -> produces observable result

evaluator
    -> applies expected transition / experiment truth afterward
```

Forbidden benchmark identifiers, ground-truth fields, expected transitions, and candidate-specific answer branches do not form part of the reasoner's semantic control path.

Gate 4 remains closed.

---

# 6. Gate 5 — Reproducibility

## Status

**CLOSED**

The measurement system was checked for reproducibility and deterministic behavior.

Repeated measurement produced identical machine-readable results.

The relevant ordering, determinism, and measurement tests passed.

A later environment-specific pytest failure involving:

```text
C:\Users\Zaid9\AppData\Local\Temp\pytest-of-Zaid9
```

was identified as a Windows temporary-directory permission problem rather than a behavioral experiment failure.

After redirecting pytest temporary files to a repository-local temporary directory, the relevant audit suite completed:

```text
27 passed
```

No research artifact was changed to obtain that result.

Gate 5 remains closed.

---

# 7. Gate 6 — External independence / provenance

## Status

**PROVENANCE CONDITION SATISFIED**

The formal specification defines Gate 6 as an external-integration boundary:

```text
External-system integration is blocked until these gates are passed.
```

It does not define a separate numerical Gate-6 score.

The acceptance addendum explicitly identified genuinely independent authorship/provenance as the immediate replication blocker.

That provenance condition has now been satisfied.

Independent fixture:

`tests/v03/gate2_independent_fixture.json`

Independent attestation:

`docs/v03-gate2-independent-author-attestation.md`

Fixture SHA-256:

```text
717B2E0D564077B7E65FFA401E337B9376E1CC50F58B5A4C962C77E81A7CDC5B
```

Attestation SHA-256:

```text
DE4C1713CE9AFE5EC6420FC9F8F8819A4EF3CC68405C870B83E3B1F6A98ED0CC
```

The provenance condition is therefore recorded as satisfied.

This does **not** authorize external-system integration because Gate 2 remains unresolved.

Recorded result:

`docs/v03-gate6-provenance-result.md`

---

# 8. Overall interpretation

The current evidence establishes:

```text
v0.2 baseline regression       CLOSED
non-circularity                CLOSED
reproducibility                CLOSED
resistance safety              PASS
independent provenance         SATISFIED
paraphrase robustness          NOT DEMONSTRATED
```

The principal unresolved question is therefore not whether the v0.3 implementation can pass the existing resistance suite.

It can.

The unresolved question is whether v0.3 demonstrates a measurable paraphrase-robustness improvement over frozen v0.2 under the frozen independent evaluation protocol.

The fresh fixture did not demonstrate that improvement because frozen v0.2 already produced zero paraphrase errors.

---

# 9. Constraints after this audit

The following must not be changed merely to convert the current Gate-2 result into a pass:

```text
Gate-2 effect-size criterion
decision tuple
independent fixture
semantic oracle
frozen v0.2 baseline
frozen v0.3 candidate
Gate-3 zero-tolerance rule
negative-control definition
```

The existing Gate-2 result remains part of the permanent experimental record.

---

# 10. External-system boundary

External-system integration remains blocked.

The experiment has not yet demonstrated the full acceptance condition required to proceed beyond the current v0.3 research boundary.

No additional H-series semantic-composition experiment is required merely to produce this acceptance audit.

No extractor redesign is justified merely by the Gate-2 0-to-0 result.

---

# 11. Next research question

The next investigation is diagnostic:

> Why did the fresh independent fixture produce zero paraphrase errors for both frozen v0.2 and frozen v0.3?

This diagnostic investigation must remain separate from the frozen acceptance result.

The accepted Gate-2 fixture and recorded result must not be altered in response to the diagnostic findings.

---

# 12. Final state

```text
Gate 1  CLOSED
Gate 2  NOT DEMONSTRATED
Gate 3  PASS
Gate 4  CLOSED
Gate 5  CLOSED
Gate 6  PROVENANCE CONDITION SATISFIED

Overall v0.3 acceptance:
NOT COMPLETE
```
