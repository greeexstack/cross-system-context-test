# v0.3 Gate 2 — Independent Fixture Authoring Brief

## Status

This document defines the independent authoring procedure for the **Gate 2 — Paraphrase Robustness** evaluation of v0.3.

It is additive to the historical independent-replication infrastructure. It does **not** replace or modify the earlier H5 replication brief or runner.

The authoritative acceptance criteria are defined in:

`docs/v03-acceptance-gates-addendum.md`

If this brief conflicts with the acceptance addendum, the acceptance addendum controls the acceptance decision.

---

## 1. Purpose

Gate 2 tests whether a frozen v0.3 candidate preserves the same downstream decision when the same secondary evidence is expressed through controlled paraphrases.

The evaluation is a **behavioral preservation test**, not a test of lexical similarity.

For each case:

1. one canonical text is supplied to the system;
2. three independently authored paraphrases express the same intended meaning;
3. the v0.2 baseline is evaluated on the canonical text and each paraphrase;
4. the frozen v0.3 candidate is evaluated on the canonical text and each paraphrase;
5. each paraphrase is compared against the canonical text using the frozen downstream decision tuple.

The canonical acceptance tuple is:

- `interpretation_class`
- `support_level`
- `decision_strength`
- `recommended_focus`

Diagnostic prose, evidence identifiers, provenance, timestamps, and internal representations are not part of Gate-2 fidelity.

---

## 2. Independence requirement

The fixture must be genuinely independently authored.

The author must not:

- inspect candidate implementation code;
- inspect candidate-specific extraction rules;
- inspect candidate-specific failure cases;
- inspect prior paraphrase failures;
- inspect prior holdout results;
- inspect post-hoc diagnostic output;
- tune wording against observed candidate behavior;
- receive the results of trial evaluations before the fixture is frozen.

The authoring environment should contain only the material necessary to understand this protocol and the fixture schema.

The author should not work from a copy of the researcher's candidate implementation when composing the text.

The research team must not provide candidate-specific examples intended to help the author produce difficult or easy cases.

The author should not be told which wording patterns the candidate handles well or poorly.

---

## 3. Required fixture structure

The acceptance population is fixed at:

- 5 semantic families;
- 1 case per family;
- 4 texts per case;
- 1 canonical text + 3 paraphrases;
- 15 canonical-to-paraphrase pairs in total.

The five required roles are:

1. `relevant`
2. `supporting`
3. `contradictory`
4. `irrelevant`
5. `service-next-step`

Do not add additional cases or remove required cases.

The machine-readable schema is defined by:

`tests/v03/gate2_acceptance_schema.py`

The independent fixture must validate against that schema before evaluation.

---

## 4. Case contents

Each case contains:

- `case_id`
- `role`
- `primary`
- `primary_state`
- `customer`
- `occurred_at`
- `texts`
- `oracle`

### 4.1 Case ID

Use a neutral external identifier.

Recommended form:

`EXT-G2-01` through `EXT-G2-05`

The identifier must not encode the semantic family or expected result.

Do not use identifiers such as:

- `RELEVANT-01`
- `CONTRADICTORY-01`
- `SERVICE-FAIL-01`

The role remains evaluator-side metadata and must not be communicated to the candidate.

### 4.2 Primary record

The primary record must contain:

- `record_id`
- `record_type`
- `customer_id`
- `summary`

The supported primary record types used by the acceptance harness include opportunity-style and service-order-style records.

The primary record establishes the pre-existing system state. It must not itself contain the secondary evidence being tested.

### 4.3 Primary state

The case must provide the pre-existing state through:

- `interpretation_class`
- `decision_strength`

This is **input state**, not the answer being evaluated.

Do not choose the primary state after examining candidate output.

### 4.4 Customer

The customer record must contain:

- `customer_id`
- `name`
- `email`
- `phone`

The customer ID must match the primary record's customer ID.

### 4.5 Timestamp

Provide a fixed `occurred_at` timestamp appropriate to the case.

The timestamp must be fixed before evaluation and must not be changed after candidate results are observed.

---

## 5. Semantic families

### 5.1 Relevant

The secondary evidence materially concerns the same work item and provides information directly relevant to the primary state.

The text should contain evidence that the system should be able to relate to the same underlying work item.

Do not make the relation explicit through labels such as "relevant evidence" or "same opportunity."

### 5.2 Supporting

The secondary evidence supports, corroborates, or advances the interpretation associated with the same work item.

The evidence should be semantically distinct from the relevant-family case while remaining internally consistent with its primary state.

### 5.3 Contradictory

The secondary evidence conflicts with an important aspect of the current interpretation.

The contradiction must be expressed naturally.

Do not write explicit meta-language such as:

- "this contradicts the previous state";
- "this is contradictory evidence";
- "the expected result should change."

The contradiction must be recoverable from the text itself.

### 5.4 Irrelevant

The secondary text concerns a different subject, project, work item, or otherwise unrelated activity.

It must be genuinely unrelated to the primary work item.

The text should not accidentally contain enough overlap to become meaningful evidence for the primary state.

The irrelevant family is intended to exercise resistance to unrelated text, but its negative-control behavior is **diagnostic** in this Gate-2 harness and is not an additional Gate-2 acceptance criterion.

### 5.5 Service-next-step

The primary record represents a completed or otherwise terminal service state in which a meaningful next step is not yet recorded.

The secondary evidence supplies information about the next operational step.

The intended next-step meaning should be preserved across all four texts.

---

## 6. Paraphrase construction

Each case must contain exactly four texts:

- Text 1 = canonical/original expression;
- Texts 2–4 = paraphrases.

All four texts must preserve the same intended semantic relation.

A paraphrase must not:

- add new facts;
- remove a material fact;
- reverse polarity;
- introduce a different entity;
- change the work item;
- change whether something is accepted or rejected;
- change whether something is complete;
- introduce or remove a requested next step;
- change the temporal meaning;
- change the identity relationship.

A paraphrase may legitimately change:

- sentence structure;
- word order;
- vocabulary;
- grammatical construction;
- level of explicitness, provided the intended meaning remains recoverable;
- active/passive voice;
- natural discourse style.

Avoid mechanical synonym substitution.

Avoid near-duplicate sentences in which only one or two words change.

Avoid preserving the exact syntax of Text 1 across all variants.

The three paraphrases should be independently written rather than generated by applying a deterministic replacement list.

---

## 7. Semantic oracle

The `oracle` is evaluator-side semantic metadata.

It must be fixed **before candidate evaluation**.

The oracle must be authored from the intended meaning of the fixture, not from observed candidate behavior.

The oracle uses the semantic fields required by the machine schema:

- `topic`
- `negated_concepts`
- `expresses_acceptance`
- `polarity`
- `confirms_approval`
- `concerns_same_work_item`
- `confirms_completion`
- `expresses_rejection`
- `requests_followup`
- `requests_next_step`

The oracle must describe the intended semantics of the text.

It must not contain:

- candidate output;
- expected candidate error;
- candidate-specific explanation;
- post-hoc correction;
- instructions for how the candidate should behave.

The oracle is evaluator-side information. It must never be supplied to the reasoning system as semantic input.

---

## 8. Blinding rules

The author must not know which text is expected to be easier or harder for either candidate.

The author must not intentionally target a known v0.3 weakness.

The author must not intentionally avoid a known v0.3 weakness.

The author must not use prior benchmark sentences as templates when those sentences were selected because of candidate behavior.

The final fixture must be frozen before the research team runs candidate evaluation.

After freezing:

- no wording changes;
- no oracle changes;
- no case removal;
- no case replacement;
- no reordering motivated by results;
- no selective reporting.

Any correction required for syntax or schema validity must occur before evaluation and must be documented.

---

## 9. Evaluation procedure

After the fixture is frozen:

1. validate the fixture against the machine schema;
2. preserve the fixture unchanged;
3. verify the frozen v0.2 source;
4. verify the frozen v0.3 candidate;
5. run the Gate-2 acceptance harness;
6. record the full output;
7. do not modify the fixture based on the result.

The acceptance harness compares each paraphrase with the canonical text using the frozen decision tuple.

For each candidate:

`errors = total_pairs - faithful_pairs`

Let:

- `E2` = v0.2 paraphrase errors;
- `E3` = v0.3 paraphrase errors.

The frozen material-improvement rule is:

`E3 <= floor(E2 / 2)`

If `E2 == 0`, Gate 2 is **not demonstrated** by an equal perfect score. A zero-error baseline does not provide evidence of material improvement.

---

## 10. What the author must deliver

The author delivers exactly one JSON fixture containing the five required cases.

The author should also provide a short attestation containing:

- author identity or research identifier;
- date of authoring;
- confirmation that the author did not inspect candidate internals;
- confirmation that the author did not receive candidate-specific failure results;
- confirmation that the fixture was frozen before evaluation.

The attestation is provenance information and does not alter the machine-scored fixture.

---

## 11. Researcher restrictions after receipt

Once the independent fixture is received, the research team must not:

- ask the author to rewrite difficult cases after seeing results;
- remove an underperforming case;
- replace a paraphrase because it exposes a failure;
- alter oracle values to match candidate output;
- tune the candidate against the fixture;
- use the fixture as a development set.

The fixture becomes the frozen Gate-2 evaluation artifact.

---

## 12. Independence boundary

This procedure is intended to establish a clean boundary between:

**Authoring**

Independent semantic construction of the fixture.

and

**Evaluation**

Execution of frozen candidates against that fixture.

The independent author supplies the semantic content.

The research team supplies the frozen acceptance protocol and executes the evaluation.

Neither side should use the evaluation result to modify the other side's work before the acceptance decision.

---

## 13. Final acceptance artifact

The final Gate-2 evidence package should contain:

1. this authoring brief;
2. the frozen independent fixture;
3. the author attestation;
4. the candidate freeze references;
5. the raw Gate-2 harness output;
6. the resulting acceptance decision.

No post-hoc selection of favorable cases is permitted.
