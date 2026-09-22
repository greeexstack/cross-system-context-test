# v0.3 H7 Cross-Record Composition Coverage Hypothesis

## Status

**Preregistered development hypothesis.**

H7 extends the already-frozen H6 composition rule to additional semantic combinations that are representable by the current `EvidenceSemantics` schema.

H7 is a development experiment and is not independent validation.

## Research question

Does the H6 cross-record composition policy preserve the same observable reasoning behavior when compatible factual semantics are distributed across different evidence records beyond the original completion + next-step case?

The experiment is restricted to semantic fields that already exist in the current production schema.

No new semantic fields are introduced for this experiment.

## Hypothesis

**H7 — Composition coverage hypothesis**

For a controlled set of compatible factual combinations:

1. each contributing evidence record has confirmed identity;
2. each contributing record is temporally valid;
3. each contributing record explicitly concerns the same work item;
4. the facts are not in unresolved positive/negative conflict;

then the production reasoner should produce the same observable decision tuple for:

* multiple separate evidence records containing the component facts;

and

* a single control record containing the equivalent joint fact set.

The observable decision tuple is:

`(interpretation_class, support_level, decision_strength, recommended_focus)`

## Primary invariant

For every eligible H7 positive case:

`decision(split_records) == decision(single_record_control)`

The split and control conditions must differ only in evidence record partitioning.

The underlying factual content of the control record must be exactly the union of the factual fields represented by the split records.

## Positive composition matrix

The initial development matrix contains these pairwise cases.

### H7-P1: approval + followup

Record A:

`confirms_approval=True`

Record B:

`requests_followup=True`

Control:

`confirms_approval=True`
`requests_followup=True`

Expected relation:

The split-record and single-record conditions must produce the same decision tuple.

### H7-P2: acceptance + followup

Record A:

`expresses_acceptance=True`

Record B:

`requests_followup=True`

Control:

`expresses_acceptance=True`
`requests_followup=True`

Expected relation:

The split-record and single-record conditions must produce the same decision tuple.

### H7-P3: completion + followup

Record A:

`confirms_completion=True`

Record B:

`requests_followup=True`

Control:

`confirms_completion=True`
`requests_followup=True`

Expected relation:

The split-record and single-record conditions must produce the same decision tuple.

### H7-P4: rejection + followup

Record A:

`expresses_rejection=True`

Record B:

`requests_followup=True`

Control:

`expresses_rejection=True`
`requests_followup=True`

This is not treated as a semantic contradiction.

The current reasoner gives rejection precedence over followup. The invariant is therefore behavioral equivalence between the split and joint representations, not an assumption that both effects must independently appear in the final result.

### H7-P5: completion + next-step

The existing H6 case is retained as a regression anchor.

It must continue to satisfy the same split-versus-control invariant.

## Negative and boundary controls

Each positive composition class must be tested against the existing H6 safety boundaries.

### Identity

A non-confirmed identity must not contribute to composition.

Test:

* valid record + `NO_MATCH`;
* valid record + `AMBIGUOUS`.

Expected behavior:

The invalid record has no compositional effect.

### Temporal validity

A stale record must not contribute to composition.

Expected behavior:

Removing the stale record must produce the same result as evaluating the valid evidence alone.

### Work-item relevance

A record with:

`concerns_same_work_item=False`

must not contribute to the composition.

### Unresolved conflict

The following must refuse composition:

* acceptance + rejection;
* positive assertion + explicit negation of the same semantic concept.

No naïve OR-combination is permitted.

### Order invariance

Reversing the order of the same eligible records must not alter the observable decision tuple.

### Determinism

Repeated evaluation of the same evidence condition must produce the same decision tuple.

### Three-record composition

At least one compatible three-record case must be evaluated.

The three-record result must match a single-record control containing the equivalent three factual fields.

## Representation boundary

The experiment must preserve evidence boundaries.

For the composition counterfactual, the implementation must continue to retain:

* contributing evidence IDs;
* contributing provenance;
* the fact that the resulting semantics originated from multiple records.

The experiment must distinguish internal provenance preservation from provenance exposed by `TransitionResult`.

No change to the public `TransitionResult` schema is part of H7.

## Measurement

The primary metric is:

`composition_equivalence_rate = equivalent positive cases / eligible positive cases`

Secondary measurements:

* invalid-record containment;
* conflict containment;
* order invariance;
* deterministic repeatability;
* three-record equivalence.

Results must be reported by composition family rather than collapsed into a single number.

## Falsification criteria

H7 is not supported under the tested development conditions if any of the following occurs:

1. an eligible positive split-record case differs from its single-record control;
2. an invalid identity, stale record, or unrelated record changes a composition result;
3. an unresolved positive/negative conflict is silently composed;
4. input order changes the result;
5. repeated evaluation is nondeterministic;
6. a three-record compatible composition fails equivalence.

A single failure is sufficient to report the relevant invariant as not established for that case.

## Scope limits

H7 does not test:

* semantic extraction quality;
* paraphrase generalization;
* independent authorship;
* independent replication;
* semantic fields absent from `EvidenceSemantics`;
* new production fields;
* external integrations.

In particular, procurement-specific composition is excluded because the current `EvidenceSemantics` schema does not contain a `procurement_progressing` field.

## Relationship to H6

H6 established the first production composition case and defined the safety policy.

H7 asks whether that policy generalizes to a broader but still controlled set of semantic combinations.

H7 does not replace, reinterpret, or modify the H6 result.

The original H6 result remains frozen.

## Experimental sequence

`hypothesis → controlled fixture → machine-checkable invariants → evaluation → result`

No production redesign should occur before the H7 fixture and invariants are frozen.

## Implementation constraint

The experiment must use the existing `EvidenceSemantics`, `SemanticEvidence`, `EvidenceCondition`, and reasoner schemas.

No benchmark labels, family identifiers, expected transition labels, or new semantic fields may be introduced into the production reasoning path.

## Validation status

H7 is a development-side coverage experiment.

Even a fully positive H7 result does not constitute independent validation.

Independent replication remains a separate validation gate.
