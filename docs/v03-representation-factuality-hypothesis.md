# v0.3 Representation Factuality Hypothesis

## Status

Pre-registered research hypothesis.

No result is implied by this document.

The unseen holdout remains frozen and is not used.

---

## 1. Research question

When the normalized extractor produces different semantic representations
for independently authored semantically equivalent development variants,
does the representation drift correspond to factual disagreement with the
explicit semantic annotations?

---

## 2. Motivation

The representation-restoration experiment established that seven observed
development behavioral changes were representation-mediated.

A separate semantic-representation invariant measurement found that only
6/15 development paraphrase pairs preserved the full semantic object.

Representation drift alone does not establish factual error.

A representation may differ while preserving every fact explicitly required
by the task.

This experiment therefore separates representation difference from factual
semantic disagreement.

---

## 3. Hypothesis H4

A substantial portion of semantically relevant representation drift will
correspond to disagreement with explicitly annotated semantic fields.

---

## 4. Null hypothesis

Representation drift frequently occurs without disagreement on explicitly
annotated semantic fields.

Under H0, many apparent representation changes are alternative
representations that preserve the explicitly specified facts.

---

## 5. Data

Use only the committed development semantic-equivalence fixtures.

The experiment may use:

- F01 equivalent pair;
- F02 equivalent pair;
- F03 equivalent pair;
- F10 equivalent pair.

The unseen holdout is excluded.

---

## 6. Annotation policy

Only fields whose expected value is explicitly specified as `True` or
`False` are evaluated.

An expected value of `None` means the fixture does not specify that fact.

`None` must not be interpreted as `False`.

No semantic facts may be inferred from the natural-language wording.

---

## 7. Measurements

For each development fixture variant measure:

- total explicitly annotated field decisions;
- exact field matches;
- field mismatches;
- factual field accuracy;
- exact projected semantic-set accuracy.

For each semantic-equivalence pair also report:

- whether the extracted full semantic representation changed;
- whether the explicitly annotated factual projection changed;
- whether either variant disagreed with the explicit annotation;
- whether the two extracted variants differ despite both being factually
  correct under the explicit annotation.

---

## 8. Interpretation

### Factual drift

The extracted representation differs from the explicit annotation on at
least one specified field.

### Benign representation drift

The complete representation differs, but all explicitly annotated fields
remain correct.

### Factual invariance

Both semantically equivalent variants preserve all explicitly annotated
facts.

---

## 9. Causal boundary

This experiment measures factual fidelity.

It does not establish:

- that a factual error caused the downstream behavioral change;
- that the extractor is the only source of semantic error;
- that every unannotated field is incorrect;
- that the semantic schema itself is inadequate.

Those require separate evidence.

---

## 10. Constraints

- development data only;
- unseen holdout untouched;
- normalized extractor unchanged;
- reasoner unchanged;
- production engine unchanged;
- no new semantic labels;
- no conversion of `None` to `False`;
- deterministic execution.

---

## 11. Decision policy

H4 receives supporting evidence only when representation drift is repeatedly
accompanied by explicit factual disagreement.

H0 remains viable when representation drift is frequently factually benign.

No threshold is declared before measurement.

The pair-level and field-level results must both be reported.

---

## 12. Next step

Implement the development factual-fidelity measurement using the existing
semantic-equivalence fixtures and the existing normalized extractor.