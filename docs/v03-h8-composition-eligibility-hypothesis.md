# v0.3 H8 Composition Eligibility and Associativity Hypothesis

## Status

**Preregistered development hypothesis.**

H8 does not replace H6 or H7.

H6 established the first production composition case.

H7 established broader semantic coverage under the tested development matrix.

H8 tests whether the composition mechanism's **eligibility boundary and grouping behavior** are themselves stable.

## Research question

Under what exact conditions may separate evidence records participate in cross-record semantic composition, and does the result remain invariant to composition grouping?

## Hypothesis

**H8 — Composition eligibility and associativity hypothesis**

Cross-record composition should occur only for evidence records that satisfy all required eligibility conditions:

1. identity is confirmed;
2. evidence is temporally valid;
3. the evidence explicitly concerns the same work item;
4. the factual assertions are compatible.

Evidence failing any required eligibility condition must not contribute factual content to the composed representation.

For eligible records, composition should be independent of record order and grouping.

## Primary invariants

### H8-I1: Unknown work-item relation exclusion

If:

`concerns_same_work_item is None`

the record is not eligible for H8 composition.

The record must not contribute factual fields to the composed result.

### H8-I2: Mixed eligibility containment

Given:

* one or more eligible records;
* one or more ineligible records;

the resulting behavior must equal the behavior obtained from the eligible records alone.

The ineligible records must have no compositional effect.

### H8-I3: Associativity

For compatible eligible evidence:

`compose(A, B, C)`

and

`compose(compose(A, B), C)`

must represent the same factual result, subject to preservation of the contributing source boundaries.

Because the current production composition object is internal, the associativity comparison may use a test-layer semantic normalization of the intermediate result.

### H8-I4: Order invariance

For the same eligible evidence set:

`compose(A, B, C) == compose(C, A, B)`

with respect to factual semantics and observable decision.

### H8-I5: Determinism

Repeated evaluation of the same evidence condition must produce the same observable decision.

## Eligibility matrix

### Eligible

* confirmed identity;
* fresh timestamp;
* `concerns_same_work_item=True`;
* compatible factual semantics.

### Ineligible

* `IdentityQuality.NO_MATCH`;
* `IdentityQuality.AMBIGUOUS`;
* stale evidence;
* `concerns_same_work_item=False`;
* `concerns_same_work_item=None`.

The `None` case is specifically tested because unknown relation is not equivalent to confirmed same-work-item relation.

## Mixed-record controls

At least three mixed conditions must be tested:

### H8-M1

Eligible completion + unknown next-step relation.

Expected:

The unknown record contributes nothing.

### H8-M2

Eligible approval + stale followup.

Expected:

The stale record contributes nothing.

### H8-M3

Eligible completion + wrong-identity next-step + eligible followup.

Expected:

Only the two eligible records contribute.

## Topic compatibility diagnostic

A separate diagnostic tests records that:

* have confirmed identity;
* are fresh;
* explicitly refer to the same work item;
* contain different topic values.

The purpose is not to assume that differing topics are incompatible.

The purpose is to determine whether the current representation contains enough information to define compatibility explicitly.

No production behavior should be changed solely because topics differ.

The result of this diagnostic must be reported separately from the primary H8 invariant.

## Associativity fixture

Use three compatible factual records.

For example:

`A = confirms_approval=True`

`B = requests_followup=True`

`C = expresses_acceptance=True`

The direct three-record composition must be compared against an equivalent grouped composition.

The grouped intermediate representation must preserve the factual fields contributed by A and B before C is incorporated.

## Provenance

The composition operation must continue to preserve:

* source evidence IDs;
* source provenance;
* record boundaries.

The experiment must distinguish:

* preservation inside the composition representation;
* provenance exposed through `TransitionResult`.

H8 does not introduce public provenance fields.

## Falsification criteria

H8 is not supported for a tested invariant if:

1. an unknown work-item relation contributes to composition;
2. an ineligible record changes the result of an eligible set;
3. composition grouping changes the factual result;
4. input order changes the factual result or decision;
5. repeated evaluation is nondeterministic;
6. source boundaries are lost during composition.

A topic mismatch by itself is not a failure; it is a diagnostic requiring an explicit compatibility interpretation.

## Scope limits

H8 does not test:

* lexical extraction;
* paraphrase generalization;
* external integrations;
* independent replication;
* semantic fields absent from the existing schema;
* unrestricted semantic reasoning.

## Methodological constraint

The experiment must begin with the existing production implementation.

No implementation modification is permitted before the H8 fixture exposes a measured invariant violation.

The experiment must remain separate from the frozen H6 and H7 result documents.

## Validation status

H8 is a development experiment.

A positive H8 result does not constitute independent validation.

The independent replication gate remains open.
