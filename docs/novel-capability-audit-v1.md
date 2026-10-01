# Novel Capability Audit v1

## Purpose
This document prevents the project from drifting into a
general-purpose AI evaluation platform.

Existing evaluation systems must be treated as research
references, not product templates.
The product must earn its differentiation through a capability
that is directly supported by our research and independently
validated.

---

## 1. What we are NOT building

We are not building another:

- generic AI evaluation platform
- LLM benchmark platform
- model comparison dashboard
- LLM-as-a-judge service
- generic custom-grader system
- production AI observability platform
- agent trace evaluation platform
- dataset management platform

These capabilities already exist in major evaluation systems.

---

## 2. Candidate problem revealed by our research

The research is concerned with a narrower problem:

A decision can depend on information distributed across multiple
systems.

When additional context becomes available, we need to determine:

1. whether the decision changed;
2. whether it should have changed;
3. whether the added context was relevant;
4. whether it belonged to the correct entity;
5. whether it was temporally valid;
6. whether the evidence supporting the change was valid;
7. whether irrelevant or invalid context incorrectly changed
   the decision.

The candidate product problem is therefore not:

"How good is this AI output?"

It is:

"Was the decision change caused by valid cross-system context,
and was that change appropriate?"

This is a research hypothesis, not yet a market claim.

---

## 3. Candidate standalone capability

Working name:

Context-Driven Decision Integrity

Core unit:

    decision
      +
    base context
      +
    additional context
      ->
    observed decision change
      ->
    decision-change integrity analysis

The intended output is not a generic quality score.

It should explain:

- what changed;
- what context caused the change;
- whether the context was valid;
- whether the change direction was expected;
- what would have happened without the context;
- what evidence supports the conclusion.

---

## 4. Proposed machine-checkable model

For a decision D:

    D_base = decision without additional context

    C = additional cross-system context

    D_context = decision with C

The evaluation must distinguish:

### Case A — justified change

    C is relevant
    C refers to the correct entity
    C is temporally valid
    C is valid evidence
    D_context differs from D_base
    direction matches the expected transition

### Case B — unjustified change

    D_context differs from D_base
    but one or more required context-integrity conditions fail

### Case C — missed change

    C satisfies the required context-integrity conditions
    but D_context fails to make the expected change

### Case D — justified resistance

    C should not change the decision
    D_context remains consistent with D_base

These four states are a candidate model and must be validated
before being exposed as product semantics.

---

## 5. Research hypothesis

### H-next

Cross-system decision changes can be evaluated as a distinct
decision-integrity problem using machine-checkable invariants
covering:

- entity identity;
- temporal validity;
- evidence validity;
- context relevance;
- expected decision direction;
- resistance to irrelevant context.

### Falsification condition

The hypothesis is not supported if these properties cannot be
defined precisely enough to produce stable machine-checkable
results on controlled cases and independent cases.

---

## 6. What must NOT happen next

We must not:

- build a larger generic benchmark simply to increase case count;
- copy the feature model of existing evaluation platforms;
- add generic LLM judges;
- add dashboards before the capability is validated;
- claim support for arbitrary customer data;
- claim production readiness;
- infer general semantic accuracy from controlled fixtures;
- turn the current 20 cases into the product itself.

The current frozen cases remain regression and research
infrastructure.

---

## 7. Next experiment

Build a small controlled fixture specifically for the candidate
capability.

The fixture must contain paired cases where:

    base decision
    +
    added context
    ->
    expected decision transition

and deliberately include:

- correct entity;
- wrong entity;
- fresh context;
- stale context;
- relevant context;
- irrelevant context;
- supporting evidence;
- conflicting evidence;
- missing context.

The first target is not scale.

The first target is proving that the proposed decision-integrity
invariants are precise, reproducible, and independently testable.

---

## 8. Product gate

Do not return to product/UI implementation until the following
are demonstrated:

1. The capability is precisely defined.
2. The capability is not merely a reimplementation of a generic
   evaluator/benchmark.
3. Controlled cases produce deterministic results.
4. Independent cases preserve the intended invariants.
5. Failure modes are diagnosable.
6. The output provides information a user could act on.

Only then should this capability become the product surface.
---

## 9. Novelty audit — current status

### Result

The current candidate capability is **not sufficiently differentiated
in its present framing**.

Recent 2026 work already addresses closely related problems:

- context integrity for agents across memory, retrieval, evidence,
  and action;
- multi-dimensional context-integrity auditing;
- provenance, freshness, lineage, and grounding;
- paired relevant-context and irrelevant-context decision changes;
- counterfactual/context-selection methods based on decision impact;
- attribution of failures to heterogeneous context sources.

Therefore:

    "context integrity"
    "decision changes when relevant context changes"
    "decision remains stable under irrelevant context"
    "cross-system context validation"

cannot by themselves be treated as our unique product capability.

### Consequence

Do NOT build the next fixture from the current candidate definition.

Do NOT productize the current "Context-Driven Decision Integrity"
label.

Do NOT increase the current case count merely to compete on scale.

### What remains potentially unexplored

The research must now identify a narrower capability that combines
properties that existing work does not already provide in the same
form.

The investigation should specifically examine whether there is a
distinct problem around:

    multiple independently-owned systems
        +
    one business decision
        +
    context arriving at different times
        +
    conflicting representations of the same entity/event
        +
    a required decision transition
        +
    machine-checkable attribution of WHICH cross-system change
    caused the transition
        +
    independent validation of that attribution

This is still only a candidate research direction.

It must not be treated as novel until the literature and product
landscape support that conclusion.

### Research gate

The next task is therefore:

    NOVELTY DISCOVERY

not implementation.

The team must identify the smallest unresolved property that:

1. is materially different from generic AI evaluation;
2. is not already adequately covered by existing context-integrity,
   provenance, benchmark, or agent-evaluation work;
3. can be expressed as a machine-checkable invariant;
4. can be tested with a controlled fixture;
5. can be independently validated.

Only after that property survives the novelty gate should a new
experimental fixture be created.
---

## 10. Refined candidate: cross-system semantic conformance

### Candidate problem

The current landscape already contains substantial work on:

- context integrity;
- provenance;
- decision traces;
- decision contracts;
- authorization;
- context selection;
- contextual counterfactuals;
- enterprise context layers.

The project therefore needs to avoid becoming another implementation
of any of these capabilities.

A narrower candidate has emerged:

> Test whether decision-relevant meaning is preserved as information
> crosses independently-owned system boundaries.

This treats the transformation between systems as the object under
test.

### Concept

A business fact may exist in one system in one representation and
reach an AI or automation system through several transformations:

    source system
        ↓
    export/API/event
        ↓
    transformation
        ↓
    normalization
        ↓
    retrieval/context assembly
        ↓
    decision

The candidate capability tests whether the semantics required by the
decision contract survive that path.

### Candidate invariants

For a decision-relevant fact F:

    Meaning(F_source) == Meaning(F_received)

does not need to mean textual equality.

Instead, the test should identify the subset of semantics that are
decision-relevant.

Possible invariants:

1. entity identity is preserved;
2. event identity is preserved;
3. temporal meaning is preserved;
4. state polarity is preserved;
5. authoritative-source status is preserved;
6. decision-relevant qualifiers are preserved;
7. contradiction relationships are preserved;
8. omission of decision-critical information is detectable.

### Controlled transition model

A fixture could define:

    source state
        +
    transformation
        ->
    received state
        ->
    expected decision behavior

Controlled perturbations should include:

- semantic-preserving transformation;
- semantic weakening;
- semantic strengthening;
- stale transformation;
- wrong-entity transformation;
- contradictory transformation;
- omitted field;
- irrelevant field injection.

The objective is to determine whether the downstream decision
responds according to the semantics that should have survived the
boundary.

### Why this may be distinct

This is not primarily:

    model evaluation

It is not primarily:

    context integrity

It is not primarily:

    provenance logging

It is not primarily:

    decision trace recording

It is not primarily:

    runtime authorization

The candidate is a conformance test for the semantic boundary between
systems and the downstream decision.

### Novelty status

UNPROVEN.

The current search did not surface a direct product or benchmark
whose primary unit is this exact cross-system semantic-conformance
relationship.

This is not sufficient evidence of novelty.

The next research task must search specifically for:

- semantic conformance testing across enterprise AI system
  boundaries;
- cross-system meaning preservation for AI decisions;
- business-fact transformation testing;
- decision-semantic drift detection across APIs/events;
- conformance testing for AI context transformations;
- invariant-based verification of decision-critical context
  transformations.

No implementation should begin until this search either:

1. identifies an existing equivalent capability, or
2. establishes a sufficiently clear unresolved gap.

### Product possibility

If validated, the eventual product would not be a generic AI
evaluation platform.

It would test an organization's AI context pathway:

    source systems
        ↓
    context transformations
    decision boundary

and identify where decision-relevant meaning is lost, changed, or
introduced incorrectly.

This is a candidate product direction only.
---

## 11. Novelty audit v2 — semantic conformance rejected

### Result

The refined candidate "cross-system semantic conformance" is also
NOT sufficiently differentiated for implementation.

The current landscape already contains substantial work covering
the major pieces of this idea.

### Existing adjacent capabilities

#### Semantic interoperability

Apache Ossie / Open Semantic Interchange is explicitly designed to
standardize semantic model exchange across analytics, AI, and BI
systems so business definitions retain consistent meaning across
tools.

This overlaps with the proposed goal of preserving business meaning
across system boundaries.

#### Data contracts

Modern data-contract specifications already define:

- schema;
- semantics;
- business rules;
- quality expectations;
- ownership;
- SLAs;
- compatibility;
- validation.

This overlaps with the proposed machine-checkable semantic
conformance layer.

#### Transformation validation

ETL/data-quality systems already perform source-to-target validation,
business-rule validation, reconciliation, transformation testing,
and semantic-equivalence checks.

This overlaps with the proposed transformation-boundary testing.

#### Context attribution

Current research already studies which context contributes to an
AI output or decision, including causal attribution and
counterfactual intervention over agent trajectories.

This overlaps with the proposed "which cross-system context caused
the decision change?" capability.

#### Metamorphic/context mutation testing

Current research already applies controlled context mutations and
metamorphic relations to RAG and agent systems.

This overlaps with the proposed controlled semantic perturbations.

#### Temporal decision consistency

Current systems and research already address:

- stale context;
- freshness;
- temporal policies;
- point-in-time consistency;
- cross-system temporal coherence;
- state-transition correctness.

This overlaps with the proposed temporal invariants.

### Conclusion

The combination of:

    cross-system data
    + semantic preservation
    + temporal validation
    + context perturbation
    + decision change

may be useful, but combination alone is not sufficient evidence
of a novel capability.

Do not build this candidate as the product.
---

## 12. What the project has learned

Two candidate product directions have now been rejected:

### Candidate 1

Context-driven decision integrity.

Rejected as insufficiently differentiated because context-integrity,
decision-boundary, context-attribution, and agent-evaluation work
already addresses large portions of the problem.

### Candidate 2

Cross-system semantic conformance.

Rejected as insufficiently differentiated because semantic-layer,
data-contract, transformation-validation, temporal-consistency,
metamorphic-testing, and attribution systems already address the
major components.

### Important implication

The project should NOT continue by combining more existing
capabilities.

For example, this would still be the wrong direction:

    semantic layer
        +
    context integrity
        +
    causal attribution
        +
    dashboard
        =
    "our unique platform"

That is feature aggregation, not a new capability.
---

## 13. New research requirement

The next research task must start from the project's own existing
experimental evidence rather than from another market category.

We need to identify a primitive that is already visible in our
research but is not merely a renamed version of an existing
capability.

The investigation must answer:

    What property of a cross-system decision can our existing
    experimental methodology test that existing semantic layers,
    data contracts, agent evaluators, metamorphic testing,
    provenance systems, and causal attribution systems do not
    directly provide?

The answer must be a property, not a collection of features.

Examples of questions to investigate:

1. What exactly does the paired base/variant structure reveal that
   ordinary context evaluation does not?

2. What does our independent negative-control methodology reveal
   that ordinary evaluation suites do not?

3. What does evaluator-independence / semantic-control isolation
   contribute that ordinary evaluation pipelines do not guarantee?

4. Is there a measurable property of a *decision transition*
   itself—not just context quality, provenance, or final-output
   quality—that remains unaddressed?

5. Can that property be expressed as a small invariant with a
   falsifiable experiment?

The project must not choose the answer in advance.
---

## 14. Current implementation status

Research only.

No new fixture should be created.

No new product capability should be implemented.

No frontend work should continue beyond keeping the prototype
buildable.

The next milestone is:

    NOVEL PRIMITIVE DISCOVERY

The primitive must survive an additional market/literature audit
before any implementation begins.