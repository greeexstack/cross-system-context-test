# v0.3 Semantic Interaction Hypothesis

## Status

Pre-registered research hypothesis.

No result is implied by this document.

The unseen holdout remains frozen and must not be used for development,
candidate tuning, threshold selection, or experiment construction.

---

## 1. Research question

Do semantic representation fields interact in ways that make independent
field repair an unreliable method for improving behavioral consistency?

---

## 2. Motivation

Prior controlled counterfactual testing produced different effects when
individual semantic fields were repaired.

Observed on the frozen unseen holdout:

- `requests_followup` improved behavioral consistency.
- `confirms_approval` improved behavioral consistency.
- `expresses_rejection` improved behavioral consistency.
- `confirms_completion` introduced regressions.
- `requests_next_step` introduced regressions.
- `concerns_same_work_item` produced no change.

These observations do not establish that semantic-field interaction is the
cause of the failures.

They only motivate a controlled interaction experiment.

---

## 3. Hypothesis H2

### H2

Semantic fields interact in the downstream reasoning pipeline such that the
behavioral effect of repairing multiple fields cannot reliably be predicted
from the effects of repairing those fields individually.

Formally, for fields A and B:

    effect(A + B) may differ from
    effect(A) + effect(B)

The experiment therefore tests whether such interaction effects are
observable.

---

## 4. Null hypothesis

### H0

Semantic fields behave independently enough that pairwise repair produces
no systematic interaction effect beyond the effects already observed from
individual repairs.

The experiment must remain capable of supporting H0.

---

## 5. Development/evaluation separation

The interaction experiment uses development evidence only.

It must not:

- inspect the unseen holdout to select fields;
- inspect unseen holdout results while constructing the experiment;
- tune candidate behavior against the unseen holdout;
- change the frozen holdout;
- change the production engine;
- change the frozen reasoner.

The unseen holdout remains an independent future evaluation.

---

## 6. Controlled comparison

For each selected semantic field pair A and B, measure:

    baseline candidate
    A repaired
    B repaired
    A+B repaired

All other inputs and reasoning components remain fixed.

The same underlying semantic oracle is used for the repair operation.

Only the selected representation fields are changed.

---

## 7. Interaction measurement

For each pair, record:

- baseline behavioral consistency;
- behavioral consistency after repairing A;
- behavioral consistency after repairing B;
- behavioral consistency after repairing A+B;
- number of genuine repairs;
- number of regressions;
- number of unchanged failures;
- number of unchanged successes.

An interaction is considered observationally present when the combined
repair behaves differently from what would be expected from treating the
individual repairs as independent.

No single numerical interaction threshold is declared in advance.

The experiment reports the complete pairwise matrix instead of collapsing it
into one score.

---

## 8. Important distinction

A pairwise interaction observation does not prove a causal mechanism inside
the reasoner.

It only establishes that changing representation fields jointly produces a
behavioral effect that cannot be understood from the corresponding
single-field experiments alone.

Mechanistic interpretation requires a separate experiment.

---

## 9. Negative controls

The experiment must verify that:

- metadata remains unchanged;
- identity remains unchanged;
- timestamps remain unchanged;
- provenance remains unchanged;
- the evaluator's expected labels are not supplied to the system under
  test;
- repair fields are derived only from the independently defined semantic
  oracle.

---

## 10. Reproducibility

The experiment must be deterministic under the declared execution
conditions.

The complete pairwise result matrix must be reproducible from the committed
code and development battery.

---

## 11. Decision policy

Possible outcomes include:

### Outcome A

Pairwise interaction effects are consistently small or absent.

Interpretation:

H2 receives no supporting evidence from this experiment.

### Outcome B

Specific field pairs show repeatable interaction effects.

Interpretation:

H2 receives evidence for localized semantic interaction.

This does not justify redesigning the representation by itself.

### Outcome C

The experiment is unstable or under-specified.

Interpretation:

No conclusion is drawn and the experiment design must be refined before
claiming evidence for or against H2.

---

## 12. Next step

Implement the pairwise interaction measurement on the development battery
using the existing semantic-repair machinery where possible.

Do not create a new semantic extractor.

Do not modify the production engine.

Do not modify the unseen holdout.