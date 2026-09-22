# v0.3 H8 Composition Eligibility and Associativity Result

## Result status

**H8 supported under the tested development conditions and controlled fixtures.**

H8 tested whether the cross-record composition mechanism has a stable eligibility boundary and whether compatible composition is invariant to record ordering and grouping.

This is development validation only. It is not independent replication.

## Hypothesis tested

H8 proposed that cross-record composition should occur only when evidence satisfies all required eligibility conditions:

1. confirmed identity;
2. temporal validity;
3. explicit same-work-item relation;
4. compatible factual assertions.

Evidence failing an eligibility condition must not contribute factual content to the composed representation.

For eligible records, composition should remain stable under:

* input-order reversal;
* repeated evaluation;
* grouping of a compatible three-record set.

## Experimental design

The H8 fixture was constructed directly against the existing semantic and evidence schemas.

The experiment specifically targeted boundaries that had not been fully established by H6 and H7:

* `concerns_same_work_item=None`;
* mixed eligible and ineligible records;
* grouped three-record composition;
* reversed composition ordering;
* repeated evaluation;
* preservation of source evidence boundaries;
* topic differences under otherwise eligible conditions.

No production semantic fields were added.

No lexical extraction was used in the H8 fixture.

## Observed results

### H8 focused fixture

The H8 eligibility and associativity fixture produced:

**21/21 tests passed.**

No H8 invariant failed after the fixture's temporal-filtering test was corrected to exercise the public `evaluate()` eligibility pipeline rather than assuming that the private composition helper performs freshness filtering.

### H6 + H7 + H8 composition regression

The combined composition suite produced:

**155/155 tests passed.**

### Full v0.3 regression

The complete v0.3 suite produced:

**1,326 passed**

**8 expected XFAILs**

**0 unexpected failures**

The eight XFAILs remain the previously documented extractor/paraphrase limitations. No new unexpected failure was introduced by H8.

## Eligibility findings

### Unknown work-item relation

Evidence with:

`concerns_same_work_item=None`

did not participate in H8 composition.

This establishes the tested distinction between:

`True = explicitly same work item`

and

`None = unknown relation`

The latter is not treated as equivalent to confirmed relevance.

### Mixed eligible and ineligible evidence

When eligible and ineligible records were presented together, the tested ineligible conditions did not change the production decision relative to the eligible records alone.

Tested ineligible cases included:

* no-match identity;
* ambiguous identity;
* stale evidence;
* explicitly different work item;
* unknown work-item relation.

This supports the tested containment invariant.

## Associativity findings

Compatible three-record composition remained semantically stable across the tested grouping arrangements.

The grouped composition result matched the direct three-record composition for the tested cases.

This establishes associativity only for the controlled semantic combinations and composition path represented in the fixture.

It does not establish universal associativity for arbitrary future semantic types.

## Order invariance

Reversing the order of eligible evidence records did not change the tested semantic result or observable decision.

This reduces dependence on incidental input ordering for the tested composition mechanism.

## Determinism

Repeated evaluation of the same evidence set produced the same semantic and observable result.

No nondeterministic behavior was observed.

## Provenance and evidence boundaries

Composition continued to retain source evidence identifiers and provenance internally.

The tested composed representation therefore preserved the source record boundaries that contributed to the result.

As established in H6 and H7, this is **internal provenance preservation**.

`TransitionResult` still does not expose provenance, so H8 does not establish externally observable provenance in the final result.

## Topic compatibility diagnostic

H8 included a diagnostic in which eligible evidence records had differing topic values while sharing:

* confirmed identity;
* fresh timestamps;
* explicit same-work-item relation.

The current implementation permitted composition and preserved the factual fields in that controlled case.

This was intentionally treated as a diagnostic rather than as proof that topic equality is either required or sufficient for semantic compatibility.

The result therefore does not justify introducing a topic-equality gate without a separate hypothesis.

## Important methodological distinction

One initial H8 fixture failure involved a stale record passed directly to the private composition helper.

That was determined to be a test-layer boundary error rather than a production-policy failure.

The reasoner architecture currently separates:

`evaluate()`

from:

`_compose_cross_record_evidence()`

with temporal eligibility enforced by `evaluate()` before composition.

The corrected H8 fixture therefore tested freshness through the production evaluation path.

This distinction is recorded so that the result does not attribute a test misuse to the production implementation.

## What H8 establishes

Under the controlled development fixtures, the current H6 composition policy has a stable tested eligibility boundary:

* confirmed identity is required;
* fresh evidence is required;
* explicit same-work-item evidence is required for composition;
* unknown work-item relation is not treated as confirmed relevance;
* invalid records do not alter the tested eligible result;
* compatible composition is deterministic;
* compatible composition is invariant to tested input ordering;
* tested three-record grouping is stable.

## What H8 does not establish

H8 does not establish:

* universal semantic compatibility;
* universal associativity across arbitrary semantic fields;
* correctness of lexical extraction;
* paraphrase robustness;
* independent replication;
* external reproducibility;
* correctness for semantic fields absent from the current schema;
* that differing topics are inherently compatible or incompatible.

The production schema still does not contain `procurement_progressing`, so that semantic combination remains outside this experiment.

## Relationship to H6 and H7

H6 established the first production cross-record composition behavior and its safety policy.

H7 expanded composition coverage across additional semantic combinations.

H8 tested the eligibility and grouping boundary underlying those results.

H8 does not modify or reinterpret the frozen H6 or H7 conclusions.

The three experiments together form a progressively broader development evidence chain:

`H6 → first production composition`

`H7 → semantic coverage`

`H8 → eligibility and grouping boundary`

## Validation status

H8 is a development-side validation.

The independently authored replication fixture is still unavailable.

Therefore H8 does not constitute independent validation or independent generalization evidence.

## Research conclusion

**H8 is supported under the tested development conditions and controlled fixtures.**

The evidence supports retaining the current eligibility boundary and tested order/grouping behavior in the v0.3 reasoning design.

However, the result remains bounded to the semantic combinations and controls actually measured.

Further changes to composition eligibility should be driven by new preregistered experiments rather than inferred from the current result.

## Frozen checkpoint

The H8 fixture was frozen in:

`ff3c892 test: add H8 composition eligibility fixture`

The repository was clean after the fixture commit.

## Final evidentiary statement

The strongest supported statement is:

> Under the preregistered H8 development conditions, the current cross-record composition mechanism excluded unknown and otherwise ineligible evidence from the tested composition path, preserved the tested source boundaries, and remained stable under record-order reversal, repeated evaluation, and controlled three-record grouping.

This is controlled development evidence, not independent validation.
