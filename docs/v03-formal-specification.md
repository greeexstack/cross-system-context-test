# v0.3 Formal Specification

**Project:** Cross-System Context Test
**Status:** Proposed specification
**Baseline protected:** `v0.2.0`
**Frozen baseline commit:** `60f125a09ffa417cdc91c1dc2c40a1dc0a17466a`

---

## 1. Purpose

v0.3 defines the next experimental version of the Cross-System Context Test.

The project is a **measurement instrument for observable behavioral response to controlled changes in cross-system evidence**.

It is not a CRM product, enterprise agent, RAG system, workflow benchmark, or vendor-specific architecture.

The core question is:

> When a system has a primary interpretation and controlled secondary evidence is introduced, removed, contradicted, invalidated, or made irrelevant, does the system make the appropriate observable state transition without making unsupported changes?

The experiment evaluates the **transition caused by the evidence condition**, not merely the correctness of an isolated final answer.

---

# 2. Research hypothesis

## Primary hypothesis

Given:

* a fixed primary state `S_p`;
* a controlled secondary evidence condition `E`;
* a known evidence relation `R`;
* a fixed evaluation procedure;

a robust system should produce an observable result `O'` whose change relative to the primary-only result `O` is consistent with the expected relation `R`.

Formally:

```text
O  = System(S_p)

O' = System(S_p + E)

Expected:
    Δ(O, O') conforms to R
```

The experiment does not claim that `E` causally caused the real-world business event.

It tests whether the **system's observable interpretation responds appropriately to the controlled evidentiary change**.

---

# 3. Definition of "justified change"

For v0.3, a change is justified when all three conditions hold:

### 3.1 Directional correctness

The change moves in the expected direction.

Examples:

```text
supporting evidence
    -> stronger / appropriately updated interpretation

contradictory evidence
    -> weaker / appropriately changed interpretation

irrelevant evidence
    -> no material change

invalid identity
    -> no unsupported change

clearly stale evidence
    -> no current-state change

secondary evidence removed
    -> movement toward primary-only state
```

### 3.2 Resistance to unsupported change

The system must not change merely because additional context exists.

Therefore unsupported changes are measured explicitly.

Examples:

```text
irrelevant context -> change       FAIL
wrong identity     -> influence    FAIL
stale evidence     -> current-use  FAIL
ambiguous identity -> confident use FAIL
missing source     -> invented evidence FAIL
```

### 3.3 Evidence-bounded strength

The system must not express a conclusion stronger than the evidence supports.

v0.3 does **not** require numerical confidence calibration.

The initial criterion is ordinal:

```text
weak evidence      -> weak/moderate support acceptable

corroborating evidence
                    -> stronger support acceptable

insufficient evidence
                    -> strong unsupported conclusion unacceptable
```

Quantitative calibration is explicitly deferred until a defensible evidentiary scale exists.

---

# 4. Experimental unit

The fundamental experimental unit is a **paired state transition**.

```text
Trial:
    (S_p, E_condition) -> O'

Comparison:
    O_base = System(S_p)
    O_variant = System(S_p + E_condition)

Measurement:
    Δ = compare(O_base, O_variant)
```

The experiment is therefore relational rather than purely absolute.

A single answer can be correct while the transition is wrong.

Example:

```text
primary-only result = A
with irrelevant evidence = A

PASS

primary-only result = A
with irrelevant evidence = B

FAIL
```

The second system may still accidentally produce a correct-looking answer in another setting, but it has demonstrated unsupported sensitivity.

---

# 5. Observable input contract

The system under test may observe:

### Primary state

Examples:

* record identifier;
* entity type;
* customer/entity identity;
* business state;
* timestamps;
* structured fields;
* primary-system text;
* other legitimate primary-system observations.

### Secondary evidence

Each secondary item may contain:

```text
evidence content
source/provenance
record identifier
entity/customer identity
timestamp
channel/type metadata
availability status
```

The observable input must **not** contain the expected behavioral label.

Forbidden examples:

```text
role = supporting
role = contradictory
expected_transition = strengthen
expected_transition = preserve
ground_truth = ...
family_id = F01
```

unless a future experiment explicitly studies the effect of exposing those fields.

---

# 6. Hidden evaluation annotations

The evaluator may maintain hidden annotations containing:

* expected evidence relation;
* expected interpretation transition;
* expected support change;
* expected resistance behavior;
* identity validity;
* temporal validity;
* missing-source expectation;
* paraphrase equivalence;
* scenario metadata.

These annotations must remain outside the system-under-test reasoning path.

The architecture must preserve:

```text
OBSERVATION PATH
data -> system under test

EVALUATION PATH
data + hidden expected behavior -> evaluator
```

These paths must not merge.

---

# 7. Evidence representation principle

v0.3 must not solve lexical dependence by simply adding answer labels to the input.

The evidence representation must preserve:

1. the underlying observable fact;
2. the source/provenance;
3. identity;
4. time;
5. availability;
6. enough natural-language content to permit genuine interpretation.

Semantic labels that directly identify the expected behavioral effect belong on the **evaluation side**, not automatically on the input side.

The representation should therefore remain **evidence-first**, not **answer-first**.

---

# 8. Minimal evidence object

The proposed conceptual evidence object is:

```text
Evidence
    source
    record_id
    entity_id / identity information
    occurred_at
    availability
    content
    optional structured attributes
```

The object should not contain a field whose primary purpose is to reveal the benchmark's expected transition.

For example:

```text
GOOD:
content = "The buyer has not approved the revised terms."
occurred_at = ...
customer_id = ...
source = ...

BAD:
role = "contradictory"
expected_effect = "weaken"
```

The first requires interpretation.

The second gives away the experiment.

---

# 9. Identity semantics

Identity must be treated independently from content semantics.

Possible states include:

```text
confident_match
ambiguous_match
no_match
```

A semantically relevant message from the wrong customer is still invalid evidence for the primary entity.

Therefore:

```text
content relevance != identity validity
```

Both dimensions must be evaluated separately.

---

# 10. Temporal semantics

Each evidence item should expose enough information to determine temporal validity.

At minimum:

```text
observed_at
experiment_time
```

The system should distinguish:

```text
fresh/current evidence
clearly stale evidence
unknown temporal validity
```

The benchmark must not encode "stale" as a hidden answer label in the observable input.

The temporal condition should be derivable from the supplied timestamps and experiment clock.

---

# 11. Availability semantics

At least three conditions must remain distinguishable:

```text
AVAILABLE_WITH_EVIDENCE

AVAILABLE_WITH_NO_RELEVANT_EVIDENCE

UNAVAILABLE
```

These are not equivalent.

In particular:

```text
UNAVAILABLE
!=
NO_COMMUNICATION
```

The system must not manufacture evidence merely because the source is missing.

---

# 12. Metamorphic relations

v0.3 should define explicit relations between paired states.

## MR-1 Relevant evidence

Changing from primary-only to relevant same-entity evidence should produce the expected change in interpretation.

```text
primary-only
    -> relevant secondary evidence
    -> justified update
```

## MR-2 Supporting evidence

Evidence that supports the existing interpretation should strengthen support without necessarily changing the interpretation class.

```text
primary-only
    -> corroboration
    -> same interpretation + stronger support
```

## MR-3 Contradictory evidence

Evidence conflicting with the primary interpretation should weaken or appropriately change the result.

```text
primary-only
    -> credible contradiction
    -> reduced support / appropriate transition
```

## MR-4 Irrelevant evidence

Evidence concerning a different matter should not materially alter the primary interpretation.

```text
primary-only
    -> irrelevant context
    -> preserve
```

## MR-5 Wrong identity

Relevant-looking evidence attached to another entity should not influence the primary interpretation.

```text
primary-only
    -> wrong-entity evidence
    -> preserve / reject
```

## MR-6 Ambiguous identity

Evidence that cannot be confidently attributed should not receive the same treatment as confirmed evidence.

```text
primary-only
    -> ambiguous evidence
    -> preserve / weaken / abstain
```

The exact permitted transition must be defined before evaluation.

## MR-7 Stale evidence

Clearly stale evidence must not automatically override current primary state.

```text
primary-only
    -> stale evidence
    -> reject current influence
```

## MR-8 Missing source

Removing availability of the secondary system must not cause invented evidence.

```text
secondary available
    -> secondary unavailable
    -> safe fallback
```

## MR-9 Evidence removal

When previously supplied secondary evidence is removed:

```text
primary + secondary
    -> primary only
```

the result should move toward the primary-only state.

## MR-10 Cross-workflow transfer

The underlying relation should survive transfer to a materially different workflow.

This tests whether the rule is genuinely about evidence/context rather than one business vocabulary.

---

# 13. Paraphrase generalization

v0.3 must explicitly test semantic-preserving paraphrase.

For a fixed evidence fact:

```text
E1 = original wording
E2 = paraphrased wording
```

the following should remain invariant when the semantics are unchanged:

```text
identity
timestamp
source
entity relationship
evidence meaning
expected transition
```

Only surface wording should vary.

The benchmark should include multiple transformations:

* synonym substitution;
* sentence restructuring;
* active/passive changes;
* different sentence ordering;
* independently authored wording;
* substantially different lexical choices.

A future system should not pass merely because it memorizes benchmark phrases.

---

# 14. Development/evaluation separation

Development and evaluation evidence must differ substantively.

Evaluation cases must not be simple copies of development cases.

They should vary:

* wording;
* entity names;
* record combinations;
* sentence structure;
* evidence composition;
* workflow context.

The evaluation system must not receive the hidden evaluation expectations.

---

# 15. Primary metrics

## 15.1 Directional Correctness

Definition:

> Percentage of paired trials in which the observed transition matches the expected direction of change.

Conceptually:

```text
Directional Correctness =
correct expected transitions
/
eligible transition trials
```

This is the primary metric.

---

## 15.2 Unsupported Change Rate

Definition:

> Percentage of trials in which the system changes materially when the correct behavior is preservation or rejection.

Especially important for:

* irrelevant context;
* stale context;
* wrong identity;
* ambiguous identity.

Lower is better.

---

## 15.3 Paraphrase Generalization Rate

Definition:

> Percentage of semantically equivalent paraphrase trials in which the system preserves the expected behavioral relation.

This directly measures the v0.2 lexical failure mode.

---

## 15.4 Evidence-Boundedness

Measures whether the system makes conclusions stronger than the available evidence supports.

This should initially be evaluated through predefined ordinal constraints rather than a fabricated numerical probability scale.

---

# 16. Secondary metrics

Where useful, additionally report:

* identity integrity;
* temporal integrity;
* missing-source safety;
* ambiguity handling;
* evidence attribution;
* reversion correctness;
* cross-workflow transfer.

These should be reported separately rather than hidden inside one aggregate score.

---

# 17. Aggregate score policy

Do **not** immediately collapse every metric into one composite number.

A single number can hide an important failure pattern.

For example:

```text
Directional Correctness = 95%
Unsupported Change Rate = 18%
```

should not be represented as an uncomplicated "95% benchmark score."

A system that often reaches the correct answer while being highly susceptible to irrelevant evidence has a materially different reliability profile.

v0.3 therefore reports the dimensions separately.

A composite score may be studied later only if there is a defensible weighting rationale.

---

# 18. Black-box requirement

The canonical evaluation is black-box.

Required interface:

```text
observable inputs
        ↓
system under test
        ↓
observable output
```

The benchmark must not require:

* internal attention inspection;
* hidden-state access;
* proprietary retrieval logs;
* internal chain-of-thought;
* implementation-specific APIs.

This makes the experiment applicable to closed and open systems.

---

# 19. White-box diagnostics

White-box instrumentation is allowed only as an auxiliary diagnostic layer when available.

Examples:

* retrieved evidence;
* tool calls;
* evidence IDs;
* intermediate structured representations;
* provenance resolution;
* internal diagnostics.

White-box data may answer:

> Why did the implementation fail?

It must not redefine:

> Did the system pass?

The canonical result remains black-box behavior.

---

# 20. Non-circularity rules

The system under test must not access:

```text
ground_truth/development.json
ground_truth/evaluation.json
expected transition
family ID
case ID as semantic information
```

Forbidden implementation strategies include:

```text
if family == "F01": ...
if pair_id == "F03-D1": ...
if role == "supporting": ...
if expected_transition == ...:
```

Also forbidden:

* fixture-specific answer phrase matching;
* hidden ground-truth lookup;
* benchmark-family-specific reasoning branches;
* treating record existence as semantic evidence.

---

# 21. V0.2 baseline treatment

`v0.2.0` remains permanently frozen.

Its existing results remain historical baseline results:

```text
repository tests: 50/50
frozen v0.2 experiment cases: 20/20
```

The lexical-generalization probe demonstrates that passing the frozen fixture set does not establish vocabulary-independent reasoning.

v0.3 must therefore be evaluated against v0.2 as a baseline rather than silently rewriting v0.2.

---

# 22. V0.3 acceptance gates

v0.3 is not considered successful merely because its original 20 cases continue to pass.

It must demonstrate improvement on independently authored paraphrase/generalization tests.

Minimum gates:

### Gate 1 — Regression safety

All frozen v0.2 cases remain passing unless an intentional specification change is explicitly documented.

### Gate 2 — Paraphrase robustness

The system must materially improve over the observed v0.2 paraphrase baseline.

The operational definition of material improvement is fixed prospectively in
`docs/v03-acceptance-gates-addendum.md`.

The Gate-2 criterion is a minimum 50% relative reduction in paraphrase error
rate on the same genuinely independent evaluation population.

Both frozen v0.2 and frozen v0.3 must be evaluated on the identical acceptance
fixture using the identical predefined decision tuple.
### Gate 3 — Resistance

Unsupported-change behavior must remain within the predefined tolerance
specified in `docs/v03-acceptance-gates-addendum.md`.

The canonical Gate-3 tolerance is zero unsupported changes in the designated
resistance population.

### Gate 4 — Non-circularity

No benchmark identifiers or ground truth may influence reasoning.

### Gate 5 — Reproducibility

The same inputs and configuration must yield reproducible results under the benchmark's declared execution conditions.

### Gate 6 — External independence

External-system integration is blocked until these gates are passed.

---

# 23. What v0.3 must NOT do

v0.3 must not become:

* a CRM benchmark;
* a general enterprise-agent benchmark;
* a large tool-calling benchmark;
* a RAG leaderboard;
* a vendor-specific integration suite;
* a generic workflow benchmark;
* a massive collection of business tasks.

Additional complexity is justified only when it improves measurement of the core evidence-transition question.

---

# 24. External-system integration gate

External systems are not selected yet.

A future source pair must satisfy:

1. it provides genuine primary/secondary evidence separation;
2. identity can be independently checked;
3. timestamps can be independently checked;
4. source availability can be manipulated or observed;
5. evidence can be controlled without changing the underlying research question;
6. the integration can be removed without changing the frozen benchmark;
7. vendor-specific benchmark tasks are not imported into the experiment.

The vendor is the environment.

The experiment remains ours.

---

# 25. Experimental sequence

Every v0.3 extension follows:

```text
research
    ↓
explicit hypothesis
    ↓
controlled fixture
    ↓
machine-checkable invariant
    ↓
implementation
    ↓
independent validation
    ↓
result
```

No implementation should precede definition of the behavioral invariant it is intended to test.

---

# 26. Immediate next experiment

Before changing the engine architecture, construct a **controlled paraphrase battery**.

The battery should:

* use existing semantic situations;
* preserve identity and timestamps;
* change only wording;
* contain independently authored paraphrases;
* include relevant, supporting, contradictory, irrelevant, and service evidence;
* contain positive and negative controls;
* remain outside the frozen v0.2 fixtures;
* be evaluated without using hidden labels as engine inputs.

Its purpose is to establish the failure distribution, not to optimize the engine against the benchmark.

Only after this measurement should the engine representation be redesigned.

---

# 27. Final design principle

The project is not trying to prove:

> "Our engine is smarter than existing enterprise agents."

It is trying to measure:

> **Whether a system responds to controlled changes in cross-system evidence in the direction warranted by that evidence, while resisting changes that are irrelevant, invalid, stale, ambiguous, or unsupported.**

That is the scientific boundary v0.3 must preserve.
