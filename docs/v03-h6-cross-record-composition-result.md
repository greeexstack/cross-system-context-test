# v0.3 H6 Cross-Record Semantic Composition Result

## Result status

**H6 supported under tested development conditions and controlled fixtures.**

This result establishes that the implemented cross-record composition policy can reproduce the tested single-record equivalent behavior for compatible evidence while enforcing the tested identity, temporal, work-item, and conflict boundaries.

This is **not independent replication** and does not establish general validity for arbitrary evidence types or deployments.

## Hypothesis tested

H6 proposed that when multiple evidence records refer to the same work item, have confirmed identity, are temporally valid, and contain compatible factual semantics, their composition should reproduce the behavior of an equivalent single evidence record expressing the same joint fact set.

The preregistered policy required:

* confirmed identity;
* temporal validity;
* explicit same-work-item relation;
* compatible factual assertions;
* preservation of source provenance and evidence boundaries.

Composition was not permitted for:

* no-match identity;
* ambiguous identity;
* stale evidence;
* unrelated work items;
* unresolved positive/negative conflict.

## Controlled experiment

The development fixture constructed semantic evidence directly against the existing `EvidenceSemantics` and `SemanticEvidence` schemas.

This intentionally separated the composition experiment from lexical extraction performance.

The principal positive control compared:

1. two separate records:

   * completion;
   * next-step request;

2. one record containing the same joint facts.

The downstream decision tuple was compared between the split-record and single-record conditions.

Additional policy-conformance cases tested identity, temporal validity, work-item relevance, provenance preservation, deterministic behavior, input-order invariance, and conflict handling.

## Observed results

### H6 composition fixture

The initial controlled fixture established:

* 10/10 H6 composition tests passed after implementation;
* the original production-equivalence XFAIL was converted into a passing invariant.

### Policy-conformance audit

The H6 policy-conformance audit produced:

* **16/16 tests passed**.

The audit initially exposed one real defect:

* explicit `expresses_acceptance=True` combined with `expresses_rejection=True` was incorrectly composable.

The implementation was corrected so this unresolved conflict blocks composition.

The corrected audit then produced:

* **16/16 tests passed**.

### Composition regression

The combined composition regression suite produced:

* **107 passed**;
* **0 failures**.

### Full v0.3 regression

After the H6 conflict-policy correction, the full v0.3 suite produced:

* **1,278 passed**;
* **8 expected XFAILs**;
* **0 unexpected failures**.

The 8 XFAILs are the already documented extractor/paraphrase limitations:

* one F10 semantic-field paraphrase limitation;
* one F10 semantic-object paraphrase limitation;
* one F02 approval paraphrase limitation;
* one F04 irrelevance paraphrase limitation;
* four previously known v0.2 lexical-generalization acceptance cases.

No new failure class was introduced by H6.

## What H6 establishes

Within the tested development fixture, the production reasoner can now combine compatible factual attributes from separate, independently represented evidence records when the records satisfy the frozen composition policy.

In particular, the tested completion + next-step split case now produces the same observable decision as the equivalent single-record joint-fact control.

The implementation also enforces the tested negative boundaries:

* non-confirmed identities are excluded;
* stale evidence is excluded;
* explicitly unrelated work items are excluded;
* ambiguous identities are excluded;
* unresolved positive/negative conflicts block composition.

The composition path retains the contributing evidence identifiers and provenance internally rather than collapsing the records into an untraceable semantic state.

## What H6 does not establish

This experiment does not establish that composition is universally safe for arbitrary semantic fields or arbitrary evidence relationships.

The current `EvidenceSemantics` schema does not contain every semantic field named elsewhere in the broader v0.3 research. In particular, the current production schema does not expose a `procurement_progressing` field, so that composition class was not directly evaluated as a production semantic-field invariant.

The current result therefore should not be generalized beyond the tested semantic combinations.

The internal `_ComposedEvidence` representation preserves source evidence IDs and provenance, but `TransitionResult` does not expose those provenance values. Therefore the experiment demonstrates **internal provenance preservation**, not externally observable provenance in the final transition result.

## Relation to prior findings

Earlier decomposition work showed that the current reasoner did not compose complementary facts when those facts were split across separate evidence records.

H6 directly targeted that boundary.

The test-layer composition experiments had already demonstrated that separate completion and next-step semantic facts could be reconstructed into the same joint fact set. H6 then moved that behavior into the production reasoning path under explicit safety constraints.

The H6 result therefore addresses a specific previously observed production boundary rather than introducing a new benchmark capability unrelated to prior evidence.

## Validation status

The result is a **development validation**, not an independent replication.

The independently authored replication fixture remains unavailable. Therefore no claim of independent generalization should be made from H6.

The strongest supported statement is:

> Under the preregistered development conditions and controlled fixtures, the H6 cross-record semantic composition policy reproduced the tested single-record equivalent behavior while passing the specified identity, temporal, work-item, conflict, determinism, and provenance-boundary checks.

## Frozen implementation checkpoints

The H6 work was frozen through the following commits:

* `8042470` — preregister H6 cross-record composition
* `12e57d4` — add H6 cross-record composition fixture
* `95a3537` — define H6 composition policy
* `306cc45` — implement H6 cross-record composition
* `1a83a90` — enforce H6 composition conflict policy

The repository was clean after the final validation run.

## Research conclusion

**H6 is supported under the tested development conditions.**

The result justifies retaining cross-record composition as part of the v0.3 reasoning design, but it does not close the generalization question.

The next research step should therefore test whether the same composition policy remains safe and behaviorally faithful across additional semantic combinations without weakening the established negative controls.

Independent replication remains a separate validation gate.
