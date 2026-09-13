# v0.3 Paraphrase Battery

**Project:** Cross-System Context Test
**Status:** Experimental design artifact
**Version:** v0.3 preliminary
**Baseline:** `v0.2.0`
**Baseline commit:** `60f125a09ffa417cdc91c1dc2c40a1dc0a17466a`

---

## 1. Purpose

This document defines the first controlled experiment for measuring the lexical-generalization weakness discovered in the v0.2 implementation.

The experiment asks:

> When the underlying evidence remains semantically unchanged, does changing only the wording preserve the system's expected behavioral response?

The experiment is designed to measure **semantic robustness**, not to improve the engine.

No source code, frozen fixtures, or v0.2 ground truth should be modified for this experiment.

---

## 2. Why this experiment exists

The frozen v0.2 fixture suite produced:

```text
20/20 PASS
```

A subsequent controlled probe changed only the wording of secondary evidence.

Five representative cases were tested.

Results:

```text
F01 relevant       -> FAILED under paraphrase
F02 supporting     -> FAILED under paraphrase
F03 contradictory -> FAILED under paraphrase
F04 irrelevant     -> PASSED under paraphrase
F10 service        -> FAILED under paraphrase
```

Observed result:

```text
4/5 failed
1/5 passed
```

This demonstrates a substantial lexical dependence in the current secondary-context interpretation layer.

The experiment below expands measurement of that problem.

---

## 3. Experimental principle

For each source evidence item, construct an original and one or more independently worded versions.

The controlled transformation is:

```text
same underlying evidence
        +
same identity
        +
same timestamp
        +
same source
        +
same entity relationship
        +
different wording
        ↓
compare system behavior
```

The semantic relationship between the evidence and the primary state must remain unchanged.

---

## 4. What must remain constant

For every paraphrase pair, hold constant:

* primary record;
* secondary record identity;
* communication ID;
* customer/entity identity;
* source;
* timestamp;
* channel;
* availability;
* evidence count;
* evidence relationship to the primary entity;
* experimental configuration;
* system version.

Only the **natural-language wording** of the evidence may change.

---

## 5. What is allowed to change

A paraphrase may change:

* word choice;
* sentence structure;
* sentence order;
* grammatical voice;
* phrasing;
* level of formality;
* syntactic construction;
* lexical register.

A paraphrase must not change:

* the underlying business fact;
* temporal meaning;
* identity;
* evidentiary strength;
* relevance;
* contradiction/support relationship;
* presence or absence of an actual decision;
* whether the evidence concerns the primary entity.

---

## 6. Evidence families to test

The initial battery should cover at least:

```text
R1  relevant evidence
R2  supporting/corroborating evidence
R3  contradictory evidence
R4  irrelevant evidence
R5  service/next-step evidence
```

Later batteries should extend this to:

```text
identity ambiguity
wrong identity
stale evidence
missing source
context removal
multiple evidence items
mixed evidence
```

The initial battery intentionally starts smaller so the experimental result remains interpretable.

---

# 7. Initial paraphrase set

## R1 — Relevant evidence

Underlying fact:

> The customer is reviewing the proposal and wants a follow-up discussion.

Original v0.2 wording:

> Customer said the proposal is under internal review and asked for a follow-up next week.

Paraphrase A:

> The customer is assessing the proposal and would like to discuss it again next week.

Paraphrase B:

> The proposal is being considered by the customer, who requested another conversation next week.

Paraphrase C:

> The customer is evaluating the offer and wants to arrange a further discussion in the coming week.

Expected semantic relation:

```text
relevant same-customer evidence
```

Expected behavioral relation:

```text
primary-only
    ->
appropriate relevant-context update
```

The exact output label is determined by the hidden evaluation contract.

---

## R2 — Supporting evidence

Underlying fact:

> The quoted amount has budget approval and procurement is progressing.

Original v0.2 wording:

> Customer confirmed the quoted amount is within the approved budget and said the proposal is moving through procurement.

Paraphrase A:

> The customer says the quoted price fits the approved budget and procurement is now progressing.

Paraphrase B:

> Budget has been authorized for the proposed amount, and the purchasing process is moving forward.

Paraphrase C:

> The customer confirmed financial approval for the quote and indicated that procurement has begun advancing it.

Expected semantic relation:

```text
supporting/corroborating evidence
```

Expected behavioral relation:

```text
same interpretation class
+
stronger support
```

---

## R3 — Contradictory evidence

Underlying fact:

> The revised commercial terms are unacceptable and the proposal should be reconsidered.

Original v0.2 wording:

> Customer said the revised commercial terms do not work for them and asked for the proposal to be revisited.

Paraphrase A:

> The customer rejected the revised commercial terms and wants the proposal reconsidered.

Paraphrase B:

> The updated pricing terms are unacceptable to the customer, who requested another review of the proposal.

Paraphrase C:

> The customer is not prepared to accept the revised terms and asked that the offer be reviewed again.

Expected semantic relation:

```text
credible contradictory evidence
```

Expected behavioral relation:

```text
reduced support
or appropriate weakening/change
```

---

## R4 — Irrelevant evidence

Underlying fact:

> The customer is discussing another project and provides no information about the quoted opportunity.

Original v0.2 wording:

> Customer discussed a separate store rollout project; no statement about the quoted opportunity.

Paraphrase A:

> The customer is discussing a different store deployment and did not comment on the current quote.

Paraphrase B:

> The conversation concerns another store rollout and contains no information about this proposal.

Paraphrase C:

> The customer raised a separate rollout initiative without providing any update on the quoted opportunity.

Expected semantic relation:

```text
irrelevant context
```

Expected behavioral relation:

```text
preserve primary interpretation
```

This is a negative control.

---

## R5 — Service / next-step evidence

Underlying fact:

> The migration workshop is complete and the customer is asking what happens in the next handoff.

Original v0.2 wording:

> Customer confirmed the migration workshop was completed and asked what the next handoff step is.

Paraphrase A:

> The customer confirmed that the migration workshop has finished and asked what the following handoff involves.

Paraphrase B:

> The migration session is complete, and the customer wants to know the next stage of the handoff.

Paraphrase C:

> The customer says the workshop is finished and is asking what should happen in the subsequent transition.

Expected semantic relation:

```text
service completion + next-step request
```

Expected behavioral relation:

```text
same service interpretation
+
next-step focus
```

---

# 8. Experimental controls

## Positive control

Run the original wording through the current engine.

The result must reproduce the known v0.2 behavior.

If it does not, the probe itself is invalid.

## Semantic-preservation control

Each paraphrase must be reviewed independently to ensure that it preserves the underlying fact.

If a paraphrase changes the meaning, it must be removed rather than counted as a model failure.

## Metadata-preservation control

Identity, timestamps, record IDs, source status, and all structured metadata must remain unchanged.

## Negative control

The irrelevant-context family should remain unchanged under paraphrase.

A useful result is therefore not merely:

```text
positive cases succeed
```

but:

```text
positive evidence still works
+
invalid/irrelevant evidence remains resisted
```

---

# 9. Measurement

For every original/paraphrase pair, record:

```text
original interpretation
original support
original strength

paraphrase interpretation
paraphrase support
paraphrase strength

behaviorally equivalent: yes/no
```

The primary measurement is:

> **Paraphrase Behavioral Consistency**

For a semantic-preserving paraphrase:

```text
PBC = 1
```

when the original and paraphrase produce the same expected behavioral relation.

Otherwise:

```text
PBC = 0
```

---

# 10. Secondary measurements

Also record:

### Directional preservation

Did the paraphrase maintain the same expected direction of change?

### Unsupported-change behavior

Did an irrelevant or invalid paraphrase introduce a new effect?

### Magnitude preservation

Did the paraphrase maintain the same qualitative strength category?

This is secondary for v0.3.

Do not require numerical confidence equivalence.

---

# 11. Failure classification

Every failure should be classified as one of:

```text
LEXICAL
```

Behavior changes because characteristic words disappear.

```text
SYNTACTIC
```

Behavior changes because sentence structure changes.

```text
SEMANTIC
```

The system appears unable to recover the underlying evidence meaning.

```text
METADATA
```

The apparent failure is actually caused by a changed or mishandled structured field.

```text
EXPERIMENTAL
```

The paraphrase did not preserve the intended semantics or another control was violated.

This classification must be determined after inspecting the result, not assumed in advance.

---

# 12. Success criterion for the diagnostic phase

This battery is a **measurement phase**, not yet an acceptance gate for a redesigned engine.

The purpose is to answer:

> How systematic is the v0.2 lexical-dependence problem?

Do not redesign the engine until this measurement is complete.

After the battery is complete, v0.3 may define a formal improvement threshold relative to v0.2.

The threshold must be based on the observed baseline rather than chosen arbitrarily beforehand.

---

# 13. What this experiment does NOT test

This battery does not measure:

* general intelligence;
* overall business-task performance;
* enterprise workflow completion;
* CRM quality;
* retrieval quality;
* tool-calling performance;
* causal reasoning;
* truth of the underlying business event.

It measures only **behavioral stability under semantics-preserving wording changes**.

---

# 14. Non-circularity requirements

The probe must not:

* modify the frozen fixtures;
* modify v0.2 ground truth;
* pass hidden expected labels into the engine;
* branch on F01-F10;
* branch on pair IDs;
* insert `supporting`, `contradictory`, `irrelevant`, or other expected labels into runtime evidence;
* use the evaluator's answer to construct the engine input.

The probe is a separate diagnostic experiment.

---

# 15. Relationship to v0.2

v0.2 remains frozen.

The paraphrase battery is not a correction to v0.2.

It establishes a new empirical observation:

```text
v0.2 frozen benchmark
    -> 20/20

independent semantic-paraphrase probe
    -> measures lexical generalization
```

Both results must remain available.

---

# 16. Relationship to v0.3 redesign

Only after the battery is measured should the redesign begin.

The redesign should attempt to replace:

```text
surface phrase detection
```

with a representation capable of preserving:

```text
evidence meaning
+
identity
+
time
+
provenance
+
availability
```

without exposing the hidden expected behavioral label.

The solution must be selected from experimental evidence.

No specific technology is mandated by this document.

---

# 17. Research discipline

The sequence is:

```text
measure failure
    ↓
classify failure
    ↓
define invariant
    ↓
propose representation
    ↓
implement
    ↓
rerun original + paraphrase + resistance tests
    ↓
compare against v0.2
```

The engine should not be redesigned simply because regexes look inelegant.

The redesign must address a measured failure.

---

# 18. Final rule

The purpose of this battery is not to make the benchmark harder.

Its purpose is to determine whether the system responds to the **meaning of evidence** or merely to the **words used to express it**.

That distinction must be established empirically before external-system integration.

**External integration remains blocked until this diagnostic phase is complete.**
# 19. Observed v0.2 Baseline Result

The initial controlled paraphrase battery was executed against the frozen v0.2 engine.

Execution conditions:

- frozen v0.2 engine;
- original fixture metadata retained;
- same primary record;
- same secondary communication ID;
- same customer identity;
- same timestamp;
- same source;
- only the communication summary wording was changed;
- no ground-truth data was supplied to the engine;
- no fixture files were modified.

Five representative cases were tested.

| Case | Evidence relation | Original result | Paraphrase result | Behavioral consistency |
|---|---|---|---|---|
| F01-D1 | Relevant | `quote_followup_pending / supported_by_secondary_context` | `quote_pending_decision / primary_only` | FAIL |
| F02-D1 | Supporting | `quote_pending_decision / secondary_supported / stronger` | `quote_pending_decision / primary_only / moderate` | FAIL |
| F03-D1 | Contradictory | `negotiation_open / weakened_by_secondary_context / weaker` | `negotiation_open / primary_only / moderate` | FAIL |
| F04-D1 | Irrelevant | `quote_pending_decision / primary_only` | `quote_pending_decision / primary_only` | PASS |
| F10-D1 | Service / next-step | `service_completed_next_step_unrecorded / supported_by_secondary_context / next_step_followup` | `service_completed_next_step_unrecorded / primary_only / no next-step focus` | FAIL |

Observed result:
## Candidate lexical-normalization result

A dependency-free candidate extractor was evaluated against the same
independently worded generalization variants used to probe the frozen
v0.2 lexical baseline.

| Case | Baseline | Candidate |
|---|---:|---:|
| F01 — follow-up | 2/3 | 3/3 |
| F02 — approval | 2/3 | 3/3 |
| F03 — rejection | 3/3 | 3/3 |
| F04 — irrelevance | 2/3 | 3/3 |
| F10 — next step | 3/3 | 3/3 |

The candidate therefore improves coverage on three cases and does not
regress on any tested case.

This result demonstrates improved lexical generalization within the
controlled battery. It does not establish genuine semantic understanding
or vocabulary-independent reasoning.

The candidate remains experimental and is not a replacement for the
frozen baseline. The paired F10 paraphrase involving "asked what the next
handoff step is" still exposes a normalization gap.