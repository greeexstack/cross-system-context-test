# v0.3 Post-Evaluation Coverage-Boundary Diagnostic

## Purpose

This document records a post-evaluation diagnostic of the frozen v0.3 clause-local extraction candidate.

It does not modify the frozen candidate, independent Gate-2 fixture, Gate-2 acceptance criterion, or any prior gate result.

## Frozen Candidate

Candidate:

`ClauseLocalRelationalEventFrameExtractor`

Relevant implementation:

- `src/experiment/v03/clause_local_extractor.py`
- `src/experiment/v03/clause_local_extractor_v2.py`

Frozen candidate state remains unchanged.

## Development-Battery Measurement

The frozen v2 extractor was evaluated against the existing 20-text development battery.

Observed:

- 20 texts
- 20 texts with frames
- 0 texts without frames
- 28 total extracted frames
- 100.0% text-level frame coverage
- 20/20 exact fact results
- 0 false-positive variants

Observed frame families:

- follow-up conversation: 4
- budget approval: 4
- procurement progression: 4
- commercial rejection: 4
- different work item: 4
- service completion: 4
- next-step/handoff request: 4

This establishes strong extraction performance within the tested development pattern domain.

## Independent Gate-2 Coverage Measurement

The independently authored Gate-2 fixture contains 20 texts across five semantic roles/cases.

The frozen v2 extractor produced:

- 0 texts with frames
- 20 texts without frames
- 0 total frames
- 0.0% text-level frame coverage

Per-case coverage:

| Case | Role | Coverage |
|---|---|---:|
| EXT-G2-01 | relevant | 0/4 |
| EXT-G2-02 | supporting | 0/4 |
| EXT-G2-03 | contradictory | 0/4 |
| EXT-G2-04 | irrelevant | 0/4 |
| EXT-G2-05 | service-next-step | 0/4 |

## Predicate-Level Diagnosis

A direct diagnostic invoked the frozen extractor's internal predicate layer on all 20 independent texts.

For every independent text:

- relevance detection returned `None`
- follow-up predicate returned `False`
- approval predicate returned `False`
- procurement predicate returned `False`
- rejection predicate returned `False`
- completion predicate returned `False`
- next-step predicate returned `False`

Therefore the independent texts were not being converted into EventFrame objects at the extraction layer.

The failure is upstream of the semantic adapter and reasoner.

## Frozen Trigger-Surface Boundary

Inspection of the frozen implementation shows that the extractor represents semantic relations through a finite set of lexical/pattern relations.

Examples include:

- approval relations centered on financial subjects plus terms such as approved, authorized, cleared, released, sanctioned, approval, authorization, clearance, or sign-off
- procurement relations centered on procurement, purchasing, buying, or sourcing plus progression terms
- commercial rejection relations centered on terms, conditions, arrangements, deals, proposals, or offers plus rejection/incompatibility language
- completion relations centered on specific service-like objects such as sessions, workshops, exercises, rollouts, implementations, deployments, migrations, and onboarding
- next-step relations centered on request/question constructions involving next-step or handoff terminology
- different-work-item relevance requiring explicit markers such as different, separate, another, or unrelated plus recognized work-item relations

The independent fixture contains semantically meaningful evidence that is often expressed outside these frozen trigger surfaces.

Examples:

### EXT-G2-01

The independent case expresses competitive proposal evaluation through vendor comparison, active review, candidate-pool reduction, and shortlist timing.

No frozen predicate represents this realization.

### EXT-G2-02

The independent case expresses funding confirmation through allocation, capital-expenditure planning, earmarked funds, and a budget line item.

These realizations do not activate the frozen approval relations.

### EXT-G2-03

The independent case expresses contradiction through recurrence of a failed repair and an unresolved compressor defect.

The frozen contradiction rules are oriented toward commercial terms, deals, proposals, offers, and related commercial incompatibility language.

### EXT-G2-04

The independent case describes a contextually different work item without using the frozen explicit different/separate/another/unrelated markers.

The frozen relevance detector therefore produces no different-work-item frame.

### EXT-G2-05

The independent case describes future delivery of a documentation package and handover, rather than the tested service-completion and customer-request constructions.

No frozen predicate activates.

## Interpretation

The evidence supports the following distinction:

`pattern-domain extraction accuracy != semantic coverage != independent generalization`

The development battery demonstrates:

> 100% tested-domain frame coverage and 20/20 exact fact recovery on the frozen development battery.

The independent fixture demonstrates:

> 0% frame coverage for the independently authored linguistic realizations used by Gate 2.

The independent result should not be characterized as a downstream reasoner failure because no secondary EventFrame evidence was produced.

The development result should not be characterized as general semantic accuracy because the tested texts exercise the extractor's finite trigger domain.

## Relationship to Gate 2

The formal Gate-2 result remains unchanged:

- v0.2 errors: 0/15
- v0.3 errors: 0/15
- Gate 2: NOT DEMONSTRATED

The 15/15 v0.3 fidelity result is compatible with a degenerate preservation path in which independent texts produce no extracted secondary evidence and the primary state is therefore preserved.

This diagnostic does not alter the frozen Gate-2 criterion.

## Scope Protection

This diagnostic does not:

- modify the frozen extractor
- modify the independent fixture
- modify the Gate-2 oracle
- modify the Gate-2 acceptance criterion
- reclassify the Gate-2 result as a pass
- create a new H-series
- introduce a new benchmark
- tune the candidate against the independent fixture

It is solely a post-evaluation explanation of the observed coverage boundary.

## Research Conclusion

The frozen v0.3 candidate has demonstrated narrow, high-accuracy recognition within its tested clause-local pattern domain.

It has not demonstrated coverage of the independently authored semantic realizations used by Gate 2.

The current evidence therefore supports the precise characterization:

> **100% tested-domain extraction accuracy; 0% demonstrated independent-fixture coverage.**
