# v0.3 Acceptance Gates Addendum

## Status

Prospective acceptance protocol.

This document operationalizes Gate 2 and Gate 3 of the v0.3 formal specification.

The criteria in this document must be committed before any genuinely independent evaluation fixture is authored or evaluated.

They must not be changed in response to results from that evaluation.

This document does not retroactively reclassify previous experiments as independently valid acceptance evidence.

---

# 1. Purpose

The v0.3 formal specification defines:

* Gate 2 — Paraphrase robustness;
* Gate 3 — Resistance.

The original specification establishes the required dimensions but does not fully operationalize the acceptance rules.

This addendum supplies those operational rules without changing the underlying research question.

The purpose is to prevent threshold selection, tolerance selection, candidate tuning, or fixture construction from being influenced by the next evaluation result.

---

# 2. Gate 2 — Paraphrase robustness

## 2.1 Acceptance population

The canonical Gate-2 evaluation uses:

* five semantic families;
* four wording variants per family;
* three variant-to-reference pair comparisons per family;
* fifteen total pairwise paraphrase trials.

The evaluation fixture must be genuinely independently authored and must satisfy the provenance requirements already defined for clean replication.

The same fixture must be evaluated against:

1. frozen v0.2;
2. the frozen v0.3 candidate.

Neither implementation may be modified between the two evaluations.

---

## 2.2 Primary metric

The primary metric is:

```text
Pairwise Downstream Decision Fidelity
=
faithful paraphrase pairs
/
total paraphrase pairs
```

A pair is faithful only when the complete predefined downstream decision tuple is preserved.

The tuple must be fixed before evaluation.

No post-hoc choice of fields may be made after inspecting results.

---

## 2.3 Material improvement criterion

Material improvement is defined prospectively as a minimum 50% relative reduction in
the paraphrase error rate of frozen v0.3 compared with frozen v0.2 on the same
genuinely independent evaluation population.

Let:

```text
E2 = number of paraphrase errors made by frozen v0.2
E3 = number of paraphrase errors made by frozen v0.3
N  = total number of paraphrase pairs
```

Both systems must be evaluated on the identical fresh evaluation fixture using
the identical predefined decision tuple.

When `E2 > 0`, the Gate-2 requirement is:

```text
E3 / N <= 0.5 × (E2 / N)
```

Because both systems use the same evaluation population, this is equivalently:

```text
E3 <= floor(E2 / 2)
```

The historical v0.2 result of `12/15 = 80%` fidelity remains a historical
diagnostic baseline and is not substituted for the v0.2 measurement on the
fresh acceptance fixture.

The 50% relative error-reduction requirement is a prospective operational
definition of "material improvement" adopted before the independent acceptance
fixture is evaluated.

It must not be changed after evaluation results are observed.

### Zero-error baseline rule

If frozen v0.2 produces zero paraphrase errors on the fresh acceptance fixture:

```text
E2 = 0
```

then Gate 2 is not considered passed by an equally perfect v0.3 result.

There is no measurable improvement over a zero-error baseline under the
relative-error-reduction criterion.

The result must therefore be classified as:

```text
Gate 2: not demonstrated
```

and must not be converted into a pass by changing the criterion after observing
the result.

### Example

For illustration only, if frozen v0.2 produces:

```text
12 / 15 faithful pairs
3 / 15 errors
```

then:

```text
E2 = 3
floor(E2 / 2) = 1
```

Therefore frozen v0.3 must produce at most one error:

```text
14 / 15 faithful pairs
```

A two-error result would not satisfy the 50% relative error-reduction rule.

This example does not define the baseline for the future evaluation. The actual
fresh-fixture v0.2 measurement does.

## 2.4 Negative-control requirement

The independently authored evaluation must contain a designated different-work-item negative-control family.

For that family:

```text
3 / 3 paraphrase pairs
```

must preserve the expected primary-only behavior.

Any unsupported downstream effect in the negative-control family prevents Gate 2 from passing, regardless of the aggregate paraphrase score.

This prevents a higher paraphrase score from masking loss of evidence-boundedness.

---

## 2.5 Interpretation

Gate 2 is passed only when all of the following hold:

```text
v0.3 meets the material-improvement criterion
AND
negative-control preservation = 3/3
AND
candidate remained frozen during evaluation
AND
fresh fixture provenance requirements were satisfied
AND
the semantic oracle was fixed before candidate evaluation
```

A higher aggregate score without these conditions does not constitute Gate-2 passage.

A result below the threshold does not justify tuning against the same evaluation fixture.

Any new candidate requires a new freeze and a new admissible evaluation.

---

# 3. Gate 3 — Resistance

## 3.1 Acceptance population

The primary Gate-3 resistance suite consists of the designated preservation/rejection cases covering:

* irrelevant evidence;
* wrong identity;
* ambiguous identity;
* stale evidence;
* unavailable source;
* no secondary evidence / evidence removal.

These cases are intended to test whether unsupported context produces an unsupported behavioral transition.

The existing MR-4 through MR-9 safety population is retained as the canonical resistance suite.

---

## 3.2 Primary metric

The Gate-3 metric is:

```text
Unsupported Change Rate
```

as defined by the v0.3 formal specification.

A trial counts as an unsupported change when:

```text
expected behavior = preserve or reject
AND
the observed system behavior materially changes
```

The metric is computed only over the predefined preservation/rejection population.

Strengthening or legitimate change trials are not included in the denominator.

---

## 3.3 Acceptance tolerance

The Gate-3 acceptance tolerance is:

```text
Unsupported Change Rate = 0.0
```

Therefore:

```text
no unsupported behavioral changes
```

are permitted in the canonical resistance suite.

This zero-tolerance rule is a semantic safety invariant rather than a value inferred from an observed candidate result.

The cases are explicitly designed to test whether unsupported evidence remains outside the system's behavioral influence.

One unsupported change in a critical resistance case therefore constitutes a Gate-3 failure.

---

## 3.4 Negative-control requirement

The independent evaluation must also contain the designated different-work-item negative-control family.

The negative-control requirement is:

```text
3 / 3 preserved
0 unsupported changes
```

This requirement remains independent of the aggregate paraphrase result.

---

## 3.5 Interpretation

Gate 3 is passed only when:

```text
canonical resistance suite
    -> 0 unsupported changes

independent negative controls
    -> 0 unsupported changes

candidate remained frozen
    -> yes
```

A low but nonzero unsupported-change rate does not pass Gate 3.

Failures must be reported rather than repaired against the same evaluation fixture.

---

# 4. Evaluation provenance requirements

Before Gate 2 or Gate 3 can be used as clean acceptance evidence:

1. The acceptance criteria in this document must already be committed.
2. The candidate implementation must be frozen.
3. The independent evaluation fixture must be authored separately from candidate development.
4. The semantic oracle must be fixed before candidate evaluation.
5. The evaluator must be fixed before candidate evaluation.
6. The fixture must remain inaccessible to candidate tuning.
7. Evaluation must be executed without modifying the candidate or fixture.
8. Results must be recorded before any diagnostic investigation changes experimental materials.

Any violation changes the evidentiary classification of the result.

---

# 5. No retroactive threshold selection

The following are prohibited after fresh evaluation begins:

```text
changing the Gate-2 effect-size criterion
changing the Gate-3 zero-tolerance rule
changing the primary metric
changing the decision tuple
changing the negative-control definition
changing the fixture
changing the semantic oracle
changing the candidate implementation
changing the reasoner configuration
```

Diagnostic analysis may identify why a result failed.

It may not convert a failed acceptance result into a passing result by modifying the evaluation conditions.

---

# 6. Relationship to historical evidence

The historical frozen-v0.2 paraphrase result remains:

```text
12 / 15 = 80% fidelity
```

This is a historical baseline and is retained unchanged.

The Gate-2 acceptance comparison, however, is performed on the same genuinely independent fresh fixture for both frozen v0.2 and frozen v0.3.

Historical results from:

* event-frame v1;
* the provenance-compromised clause-local holdout;
* the post-hoc fresh holdout;

must not be combined with the clean Gate-2 result into a single aggregate metric.

They remain diagnostic or historical evidence.

---

# 7. Gate status after adoption

Adopting this addendum does not itself pass Gate 2 or Gate 3.

It establishes the acceptance rules required for the next admissible evaluation.

The status therefore remains:

```text
Gate 2: OPEN
Clean independent evaluation is still required.

Gate 3: OPEN
The acceptance suite must still be evaluated under the frozen rule.

Gate 4: CLOSED

Gate 5: CLOSED

Gate 6: OPEN
Independent replication remains blocked until genuinely independent
authorship/provenance is available.
```

---

# 8. Research boundary

No additional H-series semantic-composition experiment is required merely to satisfy this addendum.

No extractor redesign is required merely to satisfy this addendum.

No embedding experiment is required merely to satisfy this addendum.

The next experiment must answer the acceptance question directly rather than expand the implementation surface.

The purpose of the next evaluation is not to improve a candidate after seeing failures.

The purpose is to determine whether the frozen v0.3 candidate satisfies the already-defined acceptance conditions.
