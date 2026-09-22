# v0.3 H7 Cross-Record Composition Coverage Result

## Result status

**H7 supported under the tested development conditions and controlled fixtures.**

H7 extends the H6 composition experiment across additional semantic combinations that are representable by the current `EvidenceSemantics` schema.

The result supports broader coverage of the existing H6 composition policy, but it does not establish unrestricted semantic composition or independent generalization.

## Hypothesis tested

H7 proposed that for compatible factual semantics distributed across multiple evidence records:

* identity is confirmed;
* evidence is temporally valid;
* the records explicitly concern the same work item;
* assertions are not in unresolved positive/negative conflict;

the production reasoner should produce the same observable decision tuple for split records as for a single control record containing the equivalent joint factual representation.

The observable decision tuple was:

`(interpretation_class, support_level, decision_strength, recommended_focus)`

## Experimental design

The H7 fixture constructed `SemanticEvidence` directly rather than using the lexical extractor.

This deliberately isolates the composition mechanism from extraction and paraphrase performance.

The experiment covered five positive composition families:

1. approval + followup;
2. acceptance + followup;
3. completion + followup;
4. rejection + followup;
5. completion + next-step.

The original H6 completion + next-step case was retained as a regression anchor.

A three-record positive composition was also tested.

## Primary invariant

For each eligible positive case:

`decision(split_records) == decision(single_record_control)`

The split and control cases differed only in how the same factual fields were partitioned across evidence records.

## Observed results

### H7 focused fixture

The H7 development fixture produced:

**27/27 tests passed.**

No positive composition case failed its split-versus-single-record decision equivalence invariant.

### H6 + H7 composition regression

The combined composition suite produced:

**134/134 tests passed.**

This included the existing H6 boundary suite, H6 composition fixture, H6 policy-conformance audit, and H7 coverage fixture.

### Full v0.3 regression

After adding H7, the full v0.3 suite produced:

**1,305 passed**

**8 expected XFAILs**

**0 unexpected failures**

The eight XFAILs remain the previously documented lexical extraction and paraphrase limitations. No new unexpected failure class was introduced by H7.

## Safety and boundary checks

H7 exercised the same safety boundaries established by H6.

### Identity

No-match and ambiguous identities were excluded from composition.

### Temporal validity

Stale evidence was excluded from composition.

### Work-item relevance

Evidence explicitly marked as belonging to a different work item did not contribute to the composition.

### Conflict containment

Direct acceptance + rejection conflict was refused.

Positive factual assertions combined with explicit negation of the same semantic concept were refused.

The implementation therefore did not use naïve positive-field OR-composition in those conflict cases.

### Determinism

Repeated evaluation of the same evidence condition produced the same observable decision.

### Order invariance

Reversing the order of eligible evidence records did not alter the observable decision.

### Three-record composition

A compatible three-record case was shown to reproduce the corresponding single-record control.

### Provenance and evidence boundaries

Composed evidence retained contributing evidence identifiers and provenance internally.

The source record boundaries therefore remained represented during the composition operation.

## What H7 establishes

Within the controlled development fixture, the H6 composition policy generalized beyond the original completion + next-step case to the additional tested semantic combinations.

The tested production behavior was equivalent between:

* partitioned multi-record factual representations; and
* equivalent single-record joint-fact representations.

The result therefore provides evidence that the composition mechanism is not limited to one specific semantic pair.

## What H7 does not establish

H7 does not establish that all semantic combinations can safely be composed.

The experiment is limited to semantic fields already represented by the current schema and to the specific combinations enumerated in the preregistration.

It does not test unrestricted natural-language semantic inference.

It does not test semantic extraction quality.

It does not test paraphrase robustness.

It does not introduce or validate absent fields such as `procurement_progressing`.

It does not establish external or independent reproducibility.

It does not alter the independent-replication requirement.

## Schema limitation

The current `EvidenceSemantics` schema does not expose every semantic field used elsewhere in the broader v0.3 research.

In particular, there is no `procurement_progressing` field in the current production semantic representation.

Therefore procurement-specific composition was intentionally excluded rather than simulated through an unrelated field.

## Provenance limitation

The internal `_ComposedEvidence` representation retains:

* source evidence identifiers;
* source provenance.

However, `TransitionResult` does not expose those values.

Therefore H7 establishes **internal provenance preservation**, not externally observable provenance preservation in the final transition result.

This distinction is retained from H6.

## Relationship to H6

H6 established the first production cross-record composition case and the safety policy governing composition.

H7 extended that policy to additional semantic combinations without changing the frozen H6 policy.

The H6 result remains independently recorded and is not reinterpreted by H7.

## Validation status

H7 is a development-side validation.

The independently authored replication fixture remains unavailable.

Consequently, H7 does not constitute independent replication or independent generalization evidence.

## Research conclusion

**H7 is supported under the tested development conditions and controlled fixtures.**

The evidence shows that the H6 composition policy remained behaviorally equivalent across the tested additional semantic combinations while retaining the established negative controls.

The result does not justify treating the composition mechanism as universally valid.

Further coverage should therefore proceed through new preregistered experiments rather than broadening the production composition rule without measurement.

## Frozen checkpoint

The H7 fixture was frozen in:

`37ca923 test: add H7 composition coverage fixture`

The working tree was clean after the H7 fixture commit.

## Final evidentiary statement

The strongest supported statement is:

> Under the preregistered H7 development conditions, the existing H6 cross-record composition policy reproduced single-record equivalent decisions across five tested semantic composition families and a three-record case, while passing the specified identity, temporal, work-item, conflict, order, determinism, and provenance-boundary checks.

This is controlled development evidence, not independent validation.
