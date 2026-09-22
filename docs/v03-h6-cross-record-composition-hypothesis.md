# v0.3 H6 Cross-Record Semantic Composition Hypothesis

## Purpose

Determine whether compatible factual semantics from separate evidence records can
be safely composed before downstream transition reasoning.

This experiment addresses a concrete v0.3 development finding:

* individual semantic facts can be extracted from separate records;
* the current production reasoner does not combine those facts when they are
  distributed across records;
* the same joint facts can influence reasoning when they occur on one evidence
  item.

The experiment must determine whether cross-record composition is a justified
capability and define the conditions under which it is safe.

## Research Question

When multiple evidence records contain compatible, independently valid facts
about the same work item, does composing those facts before reasoning produce
the expected transition without allowing invalid, stale, ambiguous, unrelated,
or contradictory evidence to influence the result incorrectly?

## Hypothesis

### H6 — Cross-record semantic composition

For evidence records that:

1. refer to the same intended work item;
2. have confirmed identity;
3. are temporally valid at evaluation time;
4. are available;
5. contain compatible factual semantics;

a composition layer should be able to combine their factual semantics and
produce the same downstream behavioral result that would be obtained from an
equivalent single evidence observation containing those same facts.

The hypothesis concerns semantic composition, not merely concatenation of
text.

## Primary Invariant

For compatible records A and B:

```text
compose(semantic(A), semantic(B))
```

must preserve the independently established facts from both records.

When a single-record control expresses the same complete fact set:

```text
semantic(single_record)
```

the composed representation and the single-record representation should be
equivalent with respect to the explicitly evaluated semantic fields.

The downstream reasoner should therefore produce equivalent observable
behavior for the two representations.

## Experimental Unit

Each trial contains:

```text
primary state
+
single-record control
+
multiple-record composition condition
```

The single-record control expresses the complete joint fact.

The multi-record condition distributes those facts across separate evidence
items.

All relevant metadata are fixed unless the experimental condition explicitly
changes them.

## Positive Composition Conditions

At minimum test:

### Completion + next step

Record A:

```text
confirms_completion = True
```

Record B:

```text
requests_next_step = True
```

Both records:

```text
confirmed identity
fresh
same work item
available
```

The expected joint behavior is equivalent to the single-record completion +
next-step control.

### Other compatible fact combinations

Where supported by the existing reasoner contract, test additional compatible
combinations such as:

```text
approval + supporting procurement evidence
follow-up + same-work-item relevance
```

Do not add combinations merely for coverage if their expected transition is not
specified by the existing reasoner semantics.

## Negative Controls

### Wrong identity

One record contains a compatible fact but belongs to another customer/entity.

That record must not participate in the composition.

### Ambiguous identity

One record cannot be confidently attributed to the primary entity.

It must not receive the same composition status as confirmed evidence.

### Stale evidence

A contributing record is outside the configured freshness window.

It must not influence a current composition.

### Different work item

The facts concern a separate project, opportunity, service, or workflow.

Those facts must remain semantically separate.

### Contradictory facts

Separate records provide incompatible facts.

The composition layer must not blindly combine them using simple Boolean
presence rules.

The experiment must expose the contradiction rather than converting it into an
unsupported positive joint state.

## Metadata Preservation

Composition must preserve record boundaries.

Each input record retains:

```text
evidence_id
source
record_id
identity
timestamp
availability
original content
```

Composition must not mutate the source evidence objects.

## Identity Rule

Content compatibility does not establish identity compatibility.

The composition condition may include a record only when its identity satisfies
the predefined experiment rule.

The experiment must verify:

```text
content relevance
!=
identity validity
```

## Temporal Rule

A record may contribute to composition only when it satisfies the existing
freshness policy.

A stale record must not become current merely because another record is fresh.

## Provenance Rule

Composition must retain enough provenance to determine which records supplied
each composed fact.

A composed fact without traceable source records is invalid for this
experiment.

## Conflict Rule

The experiment must not define contradiction away through Boolean aggregation.

For example:

```text
record A: approval = True
record B: approval = explicitly rejected
```

must not simply become:

```text
approval = True
```

without an explicit conflict policy.

If no conflict policy is currently specified, the correct experimental result is
that the composition layer abstains or exposes the conflict.

## Primary Measurement

### Composition equivalence

For eligible compatible cases:

```text
single-record joint representation
vs.
multiple-record composed representation
```

Measure whether the downstream observable decision tuple is exactly equivalent.

The observable decision tuple is:

```text
interpretation_class
support_level
decision_strength
recommended_focus
```

## Secondary Measurements

### Composition safety

Measure whether invalid records are prevented from contributing.

### Provenance preservation

Measure whether every composed fact can be traced to its contributing record.

### Conflict containment

Measure whether contradictory records avoid producing unsupported positive
composition.

### Determinism

Repeated composition of the same evidence set must produce the same result.

### Idempotence

Adding the same evidence record twice must not silently amplify a fact.

## Experimental Separation

This experiment does not modify the frozen v0.2 implementation.

It must not modify the existing v0.3 reasoner until the experiment design and
controls have been frozen.

A test-layer composition model may be used to establish the expected
counterfactual, but that model must not be presented as evidence that a
production composition policy is correct.

## Falsification Conditions

H6 is not supported if:

* compatible cross-record facts cannot reproduce the equivalent single-record
  behavior under controlled conditions;
* composition introduces unsupported changes in negative controls;
* conflict handling cannot prevent contradictory evidence from being combined
  incorrectly;
* identity, temporal, or provenance filtering fails;
* observed behavior depends on record ordering without an explicit reason.

## Interpretation

A positive result would establish only that the tested compatible evidence
relations can be safely composed under the tested metadata and conflict rules.

It would not establish general semantic reasoning or broad cross-workflow
generalization.

A negative result would indicate that either:

1. cross-record composition is not yet adequately specified; or
2. the current representation lacks information required for safe composition.

Those alternatives must be distinguished in a subsequent diagnostic experiment.

## Relationship to Existing Evidence

Existing v0.3 decomposition tests establish that:

* completion and next-step facts can be independently represented;
* the current reasoner recognizes the joint transition when both facts occur on
  one evidence item;
* the current reasoner does not produce that joint transition when the facts are
  distributed across separate records;
* a test-layer composition can reconstruct the joint factual set.

H6 tests the unresolved boundary between that diagnostic composition and a
justified reasoning capability.

## Research Discipline

The sequence is:

```text
hypothesis
    ↓
controlled composition fixture
    ↓
machine-checkable invariant
    ↓
test-layer counterfactual
    ↓
safe composition policy
    ↓
production implementation
    ↓
independent validation
```

No production composition behavior should be added merely because the existing
test-layer Boolean composition produces a desirable output.

## Status

H6 is preregistered as a development experiment.

No production composition capability is justified by the hypothesis alone.
