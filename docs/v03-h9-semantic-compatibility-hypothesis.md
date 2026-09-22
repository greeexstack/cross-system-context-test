# v0.3 H9 Semantic Compatibility and Conflict Hypothesis

## Status

**Preregistered development hypothesis.**

H9 follows H6, H7, and H8.

H6 established the first production cross-record composition case.

H7 expanded semantic coverage.

H8 established the tested eligibility and grouping boundary.

H9 asks the remaining question:

> When two otherwise eligible factual assertions are present, when are they actually compatible enough to be composed?

H9 does not modify the frozen H6, H7, or H8 results.

## Research question

Can the current `EvidenceSemantics` representation distinguish:

1. compatible factual assertions that should be composed;
2. genuinely conflicting assertions that must not be composed;
3. assertions whose relationship is not established by the current schema?

The objective is to prevent compatibility from being reduced to:

`same customer + fresh + same work item`

or to naïve field-wise OR-composition.

## Hypothesis

**H9 — Conservative semantic compatibility hypothesis**

For evidence records that are already eligible under the H8 boundary:

* confirmed identity;
* temporally valid;
* explicitly same work item;

composition is safe only when the semantic assertions are mutually compatible under the current representation.

Compatible assertions should reproduce the equivalent single-record control behavior.

Unresolved conflicting assertions must block composition.

Assertions whose compatibility cannot be established from the current representation must not be treated as proven compatible merely because their individual fields can be OR-combined.

## Compatibility operationalization

H9 uses an explicit controlled matrix.

A pair is classified as **compatible** when the two factual assertions can be represented simultaneously in one deliberately constructed control `EvidenceSemantics` object without requiring contradictory values for the same semantic proposition.

A pair is classified as **conflicting** when the two assertions explicitly assert opposing values of the same proposition.

A pair is classified as **undetermined** when the current schema does not contain enough information to establish whether the two assertions are compatible.

This operationalization is fixed before implementation changes.

## Primary invariant

For each preregistered compatible pair:

`decision(split_records) == decision(single_record_control)`

and:

`semantic(split_records) == semantic(single_record_control)`

for the explicitly represented factual fields.

For each conflicting pair:

`compose(split_records) == None`

No novel positive factual assertion may be produced by naïve merging.

For each undetermined pair:

The implementation must not be interpreted as evidence that the pair is semantically safe merely because composition produces a result.

## Compatible matrix

The following pairs are tested as compatible because their factual propositions are distinct and can jointly occur in one semantic representation.

### H9-C1

`confirms_approval=True`

*

`requests_followup=True`

Control:

`confirms_approval=True`
`requests_followup=True`

### H9-C2

`expresses_acceptance=True`

*

`requests_followup=True`

Control:

`expresses_acceptance=True`
`requests_followup=True`

### H9-C3

`confirms_completion=True`

*

`requests_followup=True`

Control:

`confirms_completion=True`
`requests_followup=True`

### H9-C4

`confirms_completion=True`

*

`requests_next_step=True`

Control:

`confirms_completion=True`
`requests_next_step=True`

This remains the H6 anchor.

### H9-C5

`expresses_rejection=True`

*

`requests_followup=True`

Control:

`expresses_rejection=True`
`requests_followup=True`

The final decision is expected to retain the current rejection precedence. The invariant concerns equivalence between split and joint representations, not simultaneous expression of both downstream effects.

### H9-C6

`confirms_approval=True`

*

`confirms_completion=True`

Control:

`confirms_approval=True`
`confirms_completion=True`

This is included to test composition of two state-like factual assertions that are neither the same proposition nor a previously tested H7 pair.

## Conflict matrix

### H9-X1

`expresses_acceptance=True`

*

`expresses_rejection=True`

Expected:

**refuse composition**

### H9-X2

`confirms_completion=True`

*

`negated_concepts=("completion",)`

Expected:

**refuse composition**

### H9-X3

`requests_followup=True`

*

`negated_concepts=("followup",)`

Expected:

**refuse composition**

### H9-X4

`confirms_approval=True`

*

`negated_concepts=("approval",)`

Expected:

**refuse composition**

## Topic diagnostic

Topic equality is tested separately from factual compatibility.

The experiment includes eligible records with:

* confirmed identity;
* fresh timestamps;
* `concerns_same_work_item=True`;
* different topic values;
* otherwise compatible factual assertions.

The purpose is to determine whether topic mismatch is itself sufficient evidence of semantic incompatibility.

H9 does not assume that it is.

A topic difference may be:

* compatible;
* incompatible;
* insufficiently specified.

The measured result must be reported rather than silently converted into a new policy rule.

## Negation diagnostic

Negation must remain concept-specific.

For example:

`requests_followup=True`

with:

`negated_concepts=("completion",)`

is not itself a followup conflict.

The experiment therefore tests whether unrelated negation leaves independent positive facts intact.

A conflict exists only when a positive assertion and a negated assertion refer to the same semantic concept.

## Temporal diagnostic

H9 includes an observational distinction between:

1. same-time conflicting assertions;
2. conflicting assertions with different timestamps.

The current semantic schema contains timestamps but does not explicitly encode event supersession, revision, or state-transition identity.

Therefore timestamps alone are not assumed to resolve a semantic conflict.

The experiment records this case as a diagnostic rather than introducing automatic temporal conflict resolution.

No production policy is changed on the basis of timestamp ordering alone.

## Mixed composition controls

Each compatible pair is also tested with an additional irrelevant or ineligible record.

The additional record must not change the compatible result.

Examples:

* valid approval + valid followup + wrong-identity evidence;
* valid completion + valid next-step + stale evidence;
* valid approval + valid followup + unknown work-item relation.

This reuses the H8 eligibility boundary rather than redefining it.

## Three-record compatibility

At least one three-record compatible case is included.

Example:

`approval + acceptance + followup`

The three-record split condition is compared with a single control record containing:

`confirms_approval=True`
`expresses_acceptance=True`
`requests_followup=True`

The split and control decisions must match.

## Order and grouping

Compatible H9 cases must remain invariant under record-order reversal.

At least one compatible three-record case must be tested under two grouping arrangements.

The grouping result must match the direct composition result.

## Provenance

The composed representation must continue to preserve:

* source evidence IDs;
* source provenance;
* evidence boundaries.

H9 does not change the public `TransitionResult` schema.

As in H6-H8, internal provenance preservation must not be confused with externally exposed provenance.

## Measurement

Primary measures:

`compatible_equivalence_rate`

`conflict_refusal_rate`

Secondary measures:

* unrelated-negation containment;
* topic-difference diagnostic outcome;
* timestamp-conflict diagnostic outcome;
* mixed-record containment;
* order invariance;
* grouping invariance;
* determinism;
* source-boundary preservation.

Results must be reported by matrix case.

No single aggregate score should replace the case-level results.

## Falsification criteria

H9 is not supported for a tested compatibility class if:

1. a preregistered compatible split case differs from its single-record control;
2. a preregistered conflict is silently composed;
3. unrelated negation suppresses an otherwise independent positive fact;
4. mixed ineligible records alter an eligible result;
5. input ordering changes the result;
6. grouping changes the result;
7. repeated evaluation is nondeterministic.

The topic and temporal diagnostics are not themselves failures unless the observed implementation behavior is contradicted by a preregistered invariant.

## Scope limits

H9 does not test:

* lexical extraction;
* paraphrase robustness;
* external integration;
* independent replication;
* semantic fields absent from `EvidenceSemantics`;
* automatic inference of event supersession;
* unrestricted natural-language compatibility.

In particular, no procurement-specific field is introduced.

## Methodological constraint

The existing production implementation must be evaluated before any modification.

The H9 fixture must be constructed directly from the existing semantic schema.

No new production semantic fields, compatibility labels, benchmark family IDs, or expected transition labels may enter the production reasoning path.

If an implementation failure occurs, the failed invariant must be recorded before modifying production behavior.

## Relationship to previous experiments

H6:

first production cross-record composition.

H7:

expanded semantic coverage.

H8:

eligibility, order, and grouping boundary.

H9:

semantic compatibility and conflict boundary.

Each result remains independently recorded.

## Validation status

H9 is a development experiment.

A positive result does not constitute independent validation.

The independent replication gate remains open.

## Experimental sequence

`hypothesis → controlled compatibility fixture → machine-checkable invariant → baseline evaluation → implementation decision → validation → result`

No production change should occur before the compatibility matrix has been measured against the existing implementation.
