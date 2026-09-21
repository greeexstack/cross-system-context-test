# v0.3 Representation Restoration Experiment — Result

## Status

H3 supported under the tested development conditions.

This result localizes the observed behavioral drift to the semantic
representation path for the tested behavioral-change cases.

It does not identify the deeper cause of the representation drift.

---

## 1. Experiment

For each of the 15 development paraphrase pairs, three states were compared:

### Original

Original text with its naturally extracted semantic representation.

### Paraphrase

Paraphrased text with its naturally extracted semantic representation.

### Restoration counterfactual

Paraphrased text with the original text's semantic representation restored.

The frozen v0.3 reasoner was used for all three states.

Identity, provenance, timestamp, source, and primary state remained fixed.

---

## 2. Aggregate result

Development battery:

    total pairs: 15

    representation changed: 10
    representation unchanged: 5

    behavioral changes: 7
    behavioral consistency: 8

Among the 7 behavioral-change pairs:

    representation-mediated: 7
    representation-insufficient: 0

Therefore:

    restoration success among behavioral-change pairs = 7/7

The 2 R4 representation-drift cases that did not change behavior were
classified as behaviorally masked.

---

## 3. Pair-level result

### R1-relevant

Variant 1:

    representation changed
    behavior changed
    restoration returned to original behavior

Classification:

    representation_mediated

Variant 2:

    representation unchanged
    behavior unchanged

Classification:

    no_representation_change

Variant 3:

    representation changed
    behavior changed
    restoration returned to original behavior

Classification:

    representation_mediated

---

### R2-supporting

Variant 1:

    representation changed
    behavior changed
    restoration returned to original behavior

Classification:

    representation_mediated

Variant 2:

    representation changed
    behavior changed
    restoration returned to original behavior

Classification:

    representation_mediated

Variant 3:

    representation changed
    behavior changed
    restoration returned to original behavior

Classification:

    representation_mediated

---

### R3-contradictory

All three variants:

    representation unchanged
    behavior unchanged

Classification:

    no_representation_change

---

### R4-irrelevant

Variants 1 and 2:

    representation changed
    behavior unchanged

Classification:

    behaviorally_masked

Variant 3:

    representation unchanged
    behavior unchanged

Classification:

    no_representation_change

---

### R5-service-next-step

Variant 1:

    representation unchanged
    behavior unchanged

Classification:

    no_representation_change

Variants 2 and 3:

    representation changed
    behavior changed
    restoration returned to original behavior

Classification:

    representation_mediated

---

## 4. Hypothesis result

H3 predicted:

    representation changes
        +
    behavioral changes
        +
    semantic restoration
        ->
    return to original behavior

Observed:

    7/7 behavioral-change pairs satisfied this pattern.

The experiment therefore supports H3 under the tested development conditions.

---

## 5. What this establishes

For the tested development cases, the behavioral changes observed under
paraphrase were mediated by the semantic representation supplied to the
reasoner.

The result is stronger than a simple correlation because the paraphrase
text was retained while only the semantic representation was restored.

The frozen reasoner then returned to the original observable state.

---

## 6. What this does NOT establish

This experiment does not establish:

- that the current semantic schema is optimal;
- that the extractor is the sole source of representation drift;
- that the extracted semantics are factually correct;
- that the result generalizes to the unseen holdout;
- that representation restoration would work for arbitrary inputs;
- that the event-frame candidate should replace the current extractor.

No production change is justified by this result alone.

---

## 7. Important causal boundary

The result supports the following limited statement:

    altered semantic representation
        ->
    altered downstream behavior

for the tested development cases.

It does not justify the stronger statement:

    extractor error
        ->
    behavioral failure

because the restoration experiment did not isolate every upstream
component that can affect semantic representation.

---

## 8. Relationship to previous experiments

The earlier counterfactual field-repair experiment showed that repairing
individual semantic fields produced mixed effects.

The semantic-interaction experiment did not find pairwise interaction under
its tested development conditions.

The restoration experiment now demonstrates that, for the seven observed
behavioral-change pairs, restoring the complete original semantic
representation is sufficient to restore the original behavior.

These results should not be collapsed into a single causal explanation.

---

## 9. Frozen-data policy

The unseen holdout remains untouched.

No extractor tuning was performed using the holdout.

The result is based only on the committed development battery.

---

## 10. Research conclusion

H3 is supported under the tested conditions.

The next experiment must determine whether the observed representation
drift corresponds to factual semantic errors, benign alternative
representations, or another representation-layer failure.

That question must be tested independently rather than assumed from H3.