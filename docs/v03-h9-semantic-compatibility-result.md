# v0.3 H9 Semantic Compatibility and Conflict Result

## Result status

**H9 supported under the tested development conditions and controlled fixtures.**

H9 tested whether the production composition mechanism could distinguish compatible factual assertions from unresolved conflicts, while preserving the eligibility and ordering boundaries established by H6–H8.

This is development validation only. It is not independent replication.

## Hypothesis tested

H9 proposed that, after satisfying the H8 eligibility boundary:

* confirmed identity;
* temporal validity;
* explicit same-work-item relation;

composition should occur only when the factual assertions are mutually compatible under the current semantic representation.

Compatible split records should reproduce the equivalent single-record control.

Unresolved conflicts should block composition.

## Experimental design

The H9 fixture constructed semantic evidence directly against the existing:

* `EvidenceSemantics`;
* `SemanticEvidence`;
* `EvidenceCondition`;
* production reasoner.

Lexical extraction was deliberately excluded so that H9 measured composition semantics rather than extraction quality.

The experiment covered:

### Compatible cases

* approval + followup;
* acceptance + followup;
* completion + followup;
* completion + next-step;
* rejection + followup;
* approval + completion.

### Conflict cases

* acceptance + rejection;
* positive completion + explicit completion negation;
* positive followup + explicit followup negation;
* positive approval + explicit approval negation;
* positive assertion + same-concept negation across all represented semantic fields.

### Diagnostics

* unrelated negation;
* topic differences;
* temporally separated conflicts;
* same-time conflicts;
* repeated assertions of the same positive fact.

### Boundary controls

* no-match identity;
* ambiguous identity;
* stale evidence;
* different work item;
* unknown work-item relation.

## Observed results

### H9 focused fixture

The H9 compatibility fixture produced:

**49/49 tests passed.**

No preregistered H9 compatibility or conflict invariant failed.

### H6–H9 composition regression

The combined composition suite produced:

**204/204 tests passed.**

### Full v0.3 regression

The full v0.3 suite produced:

**1,375 passed**

**8 expected XFAILs**

**0 unexpected failures**

The eight XFAILs remain the previously documented lexical extraction and paraphrase limitations.

No new unexpected failure class was introduced by H9.

## Compatibility findings

The tested compatible semantic pairs reproduced their corresponding single-record control behavior.

This included the previously established H6 completion + next-step case and the additional H7/H9 combinations.

The result therefore provides evidence that the current composition mechanism is not limited to one semantic relationship.

The evidence is still bounded to the explicit combinations tested.

## Conflict findings

The production composition mechanism correctly refused the tested unresolved conflicts.

This included:

`expresses_acceptance=True`

combined with:

`expresses_rejection=True`

and positive factual assertions combined with explicit negation of the same semantic concept.

This is important because the implementation does not simply OR every positive field and ignore polarity.

## Unrelated negation

H9 tested whether negation of one concept improperly suppresses an unrelated positive assertion.

For example:

`confirms_approval=True`

combined with:

`negated_concepts=("completion",)`

remained composable in the tested representation.

Thus negation remained concept-specific rather than acting as a global blocking signal.

## Eligibility containment

The H8 eligibility boundary remained intact during H9.

Tested invalid records did not alter the result of otherwise eligible evidence when evaluated through the production `evaluate()` path.

The tested excluded conditions were:

* no-match identity;
* ambiguous identity;
* stale evidence;
* explicit different-work-item relation;
* unknown work-item relation.

## Topic diagnostic

H9 deliberately did not assume that differing topic values automatically imply semantic incompatibility.

An eligible approval record with topic `finance` and an eligible followup record with topic `customer_contact` remained composable in the tested representation.

The resulting composed topic was not falsely collapsed into a common topic.

This remains a diagnostic rather than a proof that all cross-topic combinations are compatible.

The experiment therefore does not justify introducing topic equality as a mandatory composition gate.

## Temporal conflict diagnostic

H9 tested conflicting assertions with different timestamps.

An older acceptance and newer rejection were still refused as a composition pair.

This is consistent with the preregistered rule that timestamps alone do not establish event supersession.

The current representation does not contain an explicit revision or supersession relation.

Therefore the experiment provides no basis for automatically resolving semantic conflicts using recency alone.

## Duplicate assertions

Repeated positive assertions of the same fact remained idempotent in the tested behavior.

Adding another equivalent approval did not create a new semantic effect.

This is consistent with the factual-field representation, where the relevant assertion is represented as a boolean fact rather than an accumulating count.

## Order and determinism

The H9 fixture confirmed that tested compatible compositions were invariant to input order.

Repeated evaluation of the same evidence set produced identical semantic and observable results.

No nondeterministic behavior was observed.

## Provenance and evidence boundaries

Composition continued to preserve source evidence identifiers and provenance internally.

Source boundaries therefore remained represented in the internal composition state.

As established by H6–H8, this is **internal provenance preservation**.

`TransitionResult` still does not expose those provenance values.

H9 therefore does not establish externally observable provenance in the final transition result.

## What H9 establishes

Under the tested development conditions, the current composition mechanism supports the following bounded claims:

1. tested compatible factual combinations reproduced their single-record controls;
2. tested unresolved positive/negative conflicts were refused;
3. unrelated negation did not suppress unrelated positive facts;
4. invalid identity, temporal, and work-item conditions remained contained;
5. tested topic differences did not create false topic merging;
6. recency alone did not override semantic conflict;
7. composition remained deterministic and order-invariant for tested cases;
8. repeated identical assertions were idempotent.

## What H9 does not establish

H9 does not establish:

* universal semantic compatibility;
* universal conflict detection;
* universal conflict resolution;
* semantic correctness for fields absent from the current schema;
* automatic supersession reasoning;
* unrestricted cross-topic composition;
* lexical extraction correctness;
* paraphrase robustness;
* independent replication.

The current schema still does not expose `procurement_progressing`, so that semantic family remains outside the tested production representation.

## Important representation limitation

The current compatibility model is constrained by the expressiveness of `EvidenceSemantics`.

A semantic relationship that cannot be represented explicitly cannot be conclusively classified by this experiment.

Therefore "not detected as conflict" must not be interpreted as "proven compatible" for semantic relationships outside the tested representation.

## Relationship to H6, H7, and H8

The experiments now form a sequential development evidence chain:

### H6

Established the first production cross-record composition case and its basic safety policy.

### H7

Expanded the semantic coverage across additional tested factual combinations.

### H8

Established the tested eligibility, ordering, and grouping boundaries.

### H9

Tested semantic compatibility, conflict containment, and conservative handling of unresolved relationships.

H9 does not modify or reinterpret the earlier results.

## Validation status

H9 is development-side validation.

The independently authored replication fixture remains unavailable.

Therefore H9 does not constitute independent validation or independent generalization evidence.

## Research conclusion

**H9 is supported under the tested development conditions and controlled fixtures.**

The evidence supports the current conservative distinction between:

* factual assertions that can be combined in the tested representation;
* explicit conflicts that must block composition;
* relationships that remain outside the representation's proven compatibility guarantees.

The experiment does not justify broadening the composition rule beyond the measured semantic matrix.

## Frozen checkpoint

The H9 fixture was frozen in:

`9bbff09 test: add H9 semantic compatibility fixture`

The working tree was clean after the fixture commit.

## Final evidentiary statement

The strongest supported statement is:

> Under the preregistered H9 development conditions, the production composition mechanism reproduced single-record behavior across the tested compatible semantic combinations and refused the tested unresolved positive/negative conflicts while preserving the established eligibility, order, determinism, and internal provenance boundaries.

This is controlled development evidence, not independent validation.
