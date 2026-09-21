# v0.3 Semantic Interaction Experiment — Result

## Status

H2 not supported by the current development experiment.

This result does not prove that semantic fields never interact.

It establishes only that the committed development matrix did not expose a
repeatable pairwise interaction effect under the tested conditions.

---

## 1. Experiment

The experiment compared:

- candidate semantic representation;
- repair of field A;
- repair of field B;
- repair of fields A+B.

The same frozen v0.3 reasoner was used throughout.

The unseen holdout was not used.

Production code was not modified.

---

## 2. Observed matrix

### F01

Fields:

- `requests_followup`
- `concerns_same_work_item`

Result:

- baseline consistent
- A consistent
- B consistent
- A+B consistent

No interaction observed.

### F02

Fields:

- `confirms_approval`
- `concerns_same_work_item`

Result:

- baseline consistent
- A consistent
- B consistent
- A+B consistent

No interaction observed.

### F03

Fields:

- `expresses_rejection`
- `concerns_same_work_item`

Result:

- baseline inconsistent
- A repaired the inconsistency
- B did not repair the inconsistency
- A+B produced the same result as A

Observed interpretation:

The tested failure was localized to the represented
`expresses_rejection` field under this case.

There was no evidence that the combined repair introduced an additional
effect beyond repairing `expresses_rejection`.

### F10

Tested pairs:

- `confirms_completion` + `requests_next_step`
- `confirms_completion` + `concerns_same_work_item`
- `requests_next_step` + `concerns_same_work_item`

All tested configurations remained consistent.

No interaction observed.

---

## 3. Result

No tested pair demonstrated a pairwise interaction effect.

The experiment therefore does not support the claim:

> Semantic-field interactions are a substantial observed cause of the
> current paraphrase failures.

---

## 4. Important limitation

The experiment is a development-only diagnostic.

The tested fixture contains a limited number of explicitly specified semantic
field combinations.

Absence of observed interaction in this experiment must not be generalized
to arbitrary semantic representations or future datasets.

---

## 5. Research conclusion

H2 is not supported under the tested conditions.

The strongest case containing an observed equivalence failure, F03, was
repaired by correcting `expresses_rejection` alone.

This is evidence against treating pairwise semantic interaction as the
default explanation for the observed failure pattern.

It does not establish the underlying cause of the remaining failures.

---

## 6. Next research requirement

The next experiment must investigate the remaining unexplained failures
without tuning against the unseen holdout.

Candidate directions must be selected from measured evidence rather than
from an assumption that the failure is caused by semantic-field interaction.
