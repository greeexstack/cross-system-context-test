# v0.3 Lexical Generalization Finding

**Date:** 2026-09-13
**Observed against:** frozen v0.2.0
**Baseline commit:** `60f125a09ffa417cdc91c1dc2c40a1dc0a17466a`

## Finding

The frozen v0.2 engine can pass all 20 benchmark cases while still depending on characteristic wording from the benchmark fixtures.

A controlled paraphrase probe was run against the F01-D1 scenario.

The identity, opportunity, communication ID, and experiment timestamp were held constant.

Only the communication summary wording was changed.

### Original wording

The original communication produced:

```text
interpretation: quote_followup_pending
support: supported_by_secondary_context
decision strength: moderate
```

### Paraphrased wording

The communication summary was changed to semantically equivalent wording:

> The customer has begun evaluating the proposal and would like to arrange another discussion.

The same engine then produced:

```text
interpretation: quote_pending_decision
support: primary_only
decision strength: moderate
```

## Interpretation

The business situation represented by the secondary communication is materially the same, but the engine no longer recognized the evidence as relevant.

This demonstrates that the current v0.2 implementation contains lexical dependence that can prevent semantic generalization.

The issue is not benchmark scoring.

The issue is that the current reasoning engine uses phrase-level heuristics such as:

* `under internal review`
* `asked for a follow-up`
* `approved budget`
* `moving through procurement`
* `proposal to be revisited`
* `separate project`

These expressions closely overlap with the language used in the frozen fixture set.

## Consequence

The frozen v0.2 result remains valid as a **historical baseline**:

```text
fixture validation: PASS
v0.2 runner: 20/20 PASS
repository tests: 50/50 PASS
```

However, those results must not be interpreted as evidence that the engine is generally language-independent.

The correct conclusion is:

> v0.2 demonstrates conformance on the frozen fixture language, but its lexical-generalization capability is not established.

## Scope decision

Do not begin external-system integration yet.

The next implementation phase should investigate how to represent and reason over **evidence semantics** without relying on fixture-specific wording.

The frozen `v0.2.0` implementation must remain unchanged.

Any redesign should occur as a new version/branch so the v0.2 baseline remains reproducible.

## Required next experiment

Before redesigning the engine, create a separate paraphrase/generalization test set containing semantically equivalent observations expressed with substantially different vocabulary.

The new test set must:

* not modify the frozen fixtures;
* not use F01-F10-specific branching;
* not use ground truth as reasoning input;
* preserve identity and temporal semantics;
* vary wording independently of the expected behavioral direction;
* include both positive and negative cases;
* test whether the engine's response survives vocabulary changes.

The purpose is to determine whether the observed failure is isolated or systematic.

## Research discipline

We should not remove lexical heuristics merely because they are inelegant.

We should first measure the failure mode, define the desired invariant, and then redesign the reasoning representation.

The target is not "more complex NLP."

The target is:

> infer the evidence's role from its semantics and metadata, rather than recognizing a known benchmark phrase.

## Status

**Finding confirmed.**

**External integration blocked until lexical-generalization behavior is measured and addressed.**
