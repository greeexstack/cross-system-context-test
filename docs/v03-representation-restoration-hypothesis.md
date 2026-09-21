# v0.3 Representation Restoration Hypothesis

## Status

Pre-registered research hypothesis.

No result is implied by this document.

The unseen holdout remains frozen and is not used.

---

## 1. Research question

When a semantic representation changes between two independently authored
paraphrases and downstream behavior changes, is the behavioral change
reversible by restoring the original semantic representation while keeping
the paraphrased observation otherwise unchanged?

---

## 2. Motivation

The existing development diagnostic found:

- 15 paraphrase pairs;
- 7 behavioral-change pairs;
- 8 representation-drift pairs;
- 1 representation drift that did not change behavior;
- 0 metadata changes.

The observed association does not establish causality.

This experiment therefore tests representation restoration directly.

---

## 3. Hypothesis H3

For a paraphrase pair with:

- identical primary state;
- identical non-semantic evidence metadata;
- different extracted semantic representation;
- different downstream behavior;

restoring the original semantic representation on the paraphrased text
should restore the original downstream behavior.

---

## 4. Null hypothesis

A downstream behavioral change may persist even after restoring the original
semantic representation.

Under H0, representation restoration is insufficient to explain the
behavioral difference.

---

## 5. Controlled counterfactual

For every development paraphrase pair:

### Baseline A

Original text

    original metadata
    original extracted semantics
    frozen reasoner

### Baseline B

Paraphrase text

    identical metadata
    paraphrase-extracted semantics
    frozen reasoner

### Counterfactual C

Paraphrase text

    identical metadata
    ORIGINAL extracted semantics
    frozen reasoner

Only the semantic representation is restored in C.

No hidden semantic labels are introduced.

No unseen holdout annotations are used.

---

## 6. Measurements

For every pair record:

- representation changed;
- baseline behavior changed;
- restored behavior equals original behavior;
- restored behavior equals paraphrase behavior.

Classify each pair as:

### Representation-mediated

Behavior changed and restoration returned behavior to the original state.

### Representation-insufficient

Behavior changed and restoration did not return behavior to the original
state.

### Behaviorally masked

Representation changed but baseline behavior did not change.

### No representation change

Semantic representation remained unchanged.

---

## 7. Interpretation

A representation-mediated result supports the claim that the observed
behavioral change is transmitted through the changed semantic representation.

It does not prove that the extracted semantics are factually correct.

A representation-insufficient result means the behavior cannot be explained
by representation restoration alone.

A behaviorally masked result demonstrates that representation drift does not
necessarily propagate into an observable decision.

---

## 8. Constraints

The experiment must:

- use development data only;
- leave the unseen holdout untouched;
- use the frozen reasoner;
- use the existing extractor;
- change no production code;
- provide no hidden expected-transition labels to the reasoner;
- preserve evidence metadata;
- be deterministic.

---

## 9. Decision policy

H3 receives supporting evidence only if restoration repeatedly converts
behavioral-change cases back to their original behavior.

No fixed success threshold is declared before measurement.

The complete pair-level matrix must be reported.

---

## 10. Next step

Implement the restoration counterfactual against the existing independent
development paraphrase battery.

Do not tune the extractor based on the result.