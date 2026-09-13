# v0.2 Experiment Boundary

**Status:** Research boundary document
**Baseline protected:** `v0.2.0` (`60f125a09ffa417cdc91c1dc2c40a1dc0a17466a`)
**Date:** 2026-09-13

## 1. Purpose

This project is a **testing instrument for cross-system context-change conformance**.

It is not intended to reproduce an enterprise CRM agent, a general multi-tool agent benchmark, a retrieval benchmark, or a vendor's reasoning product.

The central question is narrower:

> When a primary-system interpretation is exposed to secondary-system context, does the system change, strengthen, weaken, or preserve its interpretation exactly as the secondary evidence justifiesâ€”and reject context that is unrelated, misattributed, ambiguous, stale, unavailable, or otherwise insufficient?

The unit of evaluation is therefore the **controlled change between paired system states**, not simply whether an agent can complete a business task.

## 2. What existing work already covers

Current work shows that several neighboring areas are already established.

### Enterprise cross-system agents

Enterprise-Bench evaluates enterprise AI agents across CRM, support, engineering, and knowledge systems. Its current L1â€“L2 suite includes cross-system retrieval and multi-source analytical reasoning, with evaluation of precision, efficiency, safety, and reliability. [1]

### CRM agent benchmarking

Salesforce's CRM benchmark evaluates sales and service use cases using real CRM data and measures accuracy, cost, speed, and trust & safety. Its accuracy evaluation includes factuality, instruction following, conciseness, and completeness. [2][3]

### Controlled perturbations are not unique by themselves

Salesforce's own benchmark uses perturbed versions of evaluation data for fairness testing, demonstrating that controlled changes to inputs are already an established evaluation technique. [3]

Therefore this project must **not** claim that any of the following is individually novel:

- cross-system enterprise reasoning;
- multi-source reasoning;
- CRM agent evaluation;
- perturbation testing;
- context robustness;
- stale-context handling;
- metamorphic testing as a general technique.

The distinction we protect must be narrower than those categories.

## 3. The experimental boundary we preserve

v0.2 is a **context-change conformance experiment**.

The experiment establishes a primary-only interpretation and then compares it against a controlled state in which secondary-system evidence has been changed.

The required response is directional:

- **change** when relevant evidence warrants a changed interpretation;
- **strengthen** when supporting evidence increases confidence without changing the interpretation class;
- **weaken** when contradictory or insufficient evidence reduces support;
- **preserve** when secondary context should not influence the primary interpretation;
- **revert toward primary-only** when the secondary context is removed.

The experiment additionally tests whether the system rejects secondary context that is:

- irrelevant;
- associated with the wrong customer;
- ambiguous in identity;
- clearly stale;
- unavailable;
- available but containing no relevant communication/evidence.

The evaluation therefore focuses on **how the interpretation responds to controlled evidence changes**, not only whether a single final answer is correct.

## 4. Explicit non-goals

This project does not attempt to build:

- a CRM;
- a CRM replacement;
- an email intelligence product;
- a customer-support platform;
- a generic enterprise agent;
- a general RAG benchmark;
- a generic tool/API-calling benchmark;
- a broad enterprise workflow benchmark;
- a vendor-specific agent architecture;
- a customer-enrichment system;
- a causal/root-cause analysis engine.

Existing products, benchmarks, papers, and platforms may be used as **research references only**.

We do not copy their architecture, import their components, reproduce their task suites, or make their evaluation framework the architecture of this project.

## 5. The specific properties we measure

The frozen v0.2 evaluation dimensions are:

`context_sensitivity`
`context_resistance`
`direction_correctness`
`evidence_validity`
`identity_integrity`
`temporal_integrity`
`ambiguity_handling`
`missing_data_handling`
`generalization`

These dimensions are interpreted jointly.

For example, correctly using relevant context is insufficient if the same system also accepts wrong-customer or stale context.

## 6. Why paired states matter

The primary comparison is:

```text
primary-only interpretation
        versus
primary + controlled secondary context
