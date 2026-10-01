# Novel Capability Audit v2 — Novelty Closure

## Status

**Research conclusion: no novel standalone capability has been established.**

This document closes the current novelty-discovery branch without modifying the frozen v0.2 baseline, v0.3 acceptance protocol, completed evaluation fixtures, or prior experimental results.

The purpose is to distinguish:

- capabilities demonstrated by this project;
- capabilities already substantially represented by existing research or products;
- properties that remain technically interesting but are not yet established as novel.

This is a **targeted novelty audit, not a claim of exhaustive literature coverage**.

---

## 1. Research starting point

The project investigated whether its controlled cross-system decision methodology could support a capability distinct from generic AI evaluation.

The research path considered:

1. context-driven decision integrity;
2. cross-system semantic conformance;
3. decision-transition attribution/witness;
4. semantic-preserving transformation testing;
5. cross-record semantic composition;
6. identity and event-identity preservation;
7. cross-source conflict and provenance handling.

The project deliberately rejected feature aggregation as a novelty basis.

The existing research record explicitly states that combining semantic layers, context integrity, causal attribution, provenance, and dashboards does not establish a new capability. The required object of discovery is a **property**, not a collection of features.

---

## 2. Candidate 1 — Context-driven decision integrity

### Candidate

The initial candidate was:

> Determine whether a decision change was caused by valid cross-system context and whether that change was appropriate.

The proposed invariants included identity validity, temporal validity, evidence validity, relevance, expected direction, and resistance to irrelevant context.

### Project evidence

The project developed paired base/variant decision experiments and machine-checkable transition relations covering relevant, supporting, contradictory, irrelevant, wrong-identity, ambiguous, stale, unavailable, and evidence-removal conditions.

### External overlap

Recent work already evaluates evidence dependence by systematically removing cited evidence and observing whether LLM predictions revise accordingly. Fact-Ablated Evaluation explicitly investigates whether strong prediction accuracy is actually dependent on supplied evidence.

Recent work also evaluates decision-critical context through counterfactual selection and removal. Decision-Aware Memory Cards measures action-critical evidence and reports the effect of removing high-utility context units.

### Conclusion

**Not sufficiently differentiated.**

The project's controlled decision-change measurement is useful research methodology, but the general property “decision changes appropriately when relevant evidence changes and remains stable when irrelevant evidence changes” is already represented by evidence-ablation and counterfactual/context-attribution research.

---

## 3. Candidate 2 — Cross-system semantic conformance

### Candidate

The second candidate reframed the problem as:

> Test whether decision-relevant meaning is preserved as information crosses independently owned system boundaries.

The proposed invariants covered identity, event identity, temporal meaning, polarity, authority, qualifiers, contradiction relationships, and omission of critical information.

### Project evidence

The project investigated semantic representations, cross-record composition, eligibility, compatibility, conflict containment, temporal validity, identity, provenance, and work-item relevance.

H6–H9 established bounded composition properties under controlled development fixtures, while explicitly limiting those conclusions to the tested semantic fields and combinations. H7, H8, and H9 specifically disclaim universal semantic compatibility, unrestricted extraction, paraphrase robustness, and independent generalization.

### External overlap

Enterprise data-contract and semantic-interoperability work already addresses machine-readable semantics, business definitions, context, interoperability, governance, and AI-ready data products. Current 2026 industry material describes data-product contracts being used to generate semantic layers and enterprise knowledge graphs for AI systems.

Cross-source evidence adjudication also directly addresses heterogeneous evidence, provenance, source quality, conflicts, and preserve/revise decisions. CLEAR is a current 2026 example.

### Conclusion

**Not sufficiently differentiated.**

Cross-system semantic preservation is a meaningful engineering problem, but the current candidate is substantially covered by semantic interoperability, data contracts, cross-source evidence adjudication, and related provenance/validation work.

---

## 4. Candidate 3 — Decision-transition witness

### Candidate

The narrower proposal was:

> Establish that a specific distributed evidence delta is the necessary and sufficient witness for a particular decision transition.

A proposed controlled relation was:

```text
S0
  +
all evidence
  -> D1

remove ΔE
  -> D0

retain ΔE while removing unrelated evidence
  -> D1

replace ΔE with invalid/stale/wrong-entity evidence
  -> D0
```

The motivation was to move beyond simply asking whether a decision changed and instead identify the particular evidence delta associated with the transition.

### Project evidence

The repository already implements paired-state observation, transition direction, evidence removal, negative controls, identity controls, temporal controls, and controlled evidence conditions.

### External overlap

The current research landscape contains several close mechanisms.

Fact-Ablated Evaluation repeatedly ablates evidence and evaluates whether predictions change, directly testing evidence dependence.

A 2026 black-box framework measures per-message counterfactual attribution at multi-agent decision points, explicitly asking whether an individual message drives a downstream action and controlling for sampling noise.

Decision-aware context work also evaluates individual evidence units by action shift, outcome uplift, necessity, and negative-transfer risk, including removal of high-utility evidence.

### Conclusion

**Not sufficiently differentiated in its current form.**

The proposed witness relation is narrower and potentially useful, but the core operation—controlled evidence intervention followed by measurement of downstream decision change—is already represented in current evidence-ablation and counterfactual attribution work.

A genuinely novel claim would therefore require a further property that those methods do not directly provide.

---

## 5. Candidate 4 — Semantic-preserving transformation / paraphrase robustness

### Candidate

The project investigated whether decision behavior survives semantic-preserving changes in wording and independently authored paraphrases.

### Project evidence

The project created fresh holdouts, pairwise downstream decision fidelity measurements, independent replication, and a frozen Gate-2 acceptance protocol.

The final Gate-2 acceptance result was:

```text
v0.2: 15/15 faithful
v0.3: 15/15 faithful
E2 = 0
E3 = 0

Gate 2: NOT DEMONSTRATED
```

The acceptance protocol correctly prevents an equally perfect v0.3 result from being converted into a demonstrated improvement over a zero-error v0.2 baseline.

### External overlap

Semantic invariance and metamorphic testing for agentic AI explicitly evaluate whether semantically equivalent transformations preserve behavior, including paraphrase, reordering, expansion, contraction, business-context transformations, and contrastive formulations.

A 2026 systematic survey describes metamorphic testing as an established approach for evaluating LLM and agent behavior where relations among executions provide the evaluation oracle.

### Conclusion

**Not novel as a standalone capability.**

The project's evaluation discipline is useful, but semantic-preserving transformation testing already exists as an active research area.

---

## 6. Candidate 5 — Cross-record semantic composition

### Candidate

H6–H9 investigated whether complementary facts represented in separate evidence records could be safely composed while respecting:

- identity;
- freshness;
- work-item relevance;
- compatibility;
- contradiction;
- ordering;
- provenance;
- deterministic behavior.

### Project evidence

H6, H7, H8, and H9 were supported under controlled development conditions. Their own result documents explicitly limit the conclusions to tested semantic combinations and disavow universal semantic compatibility, extraction correctness, paraphrase robustness, and independent replication.

### External overlap

Cross-source evidence systems already address combining evidence from heterogeneous sources while considering provenance, source quality, agreement, conflict, and revision.

Entity-resolution products already match and link records across applications, channels, and data stores to create unified entity views.

### Conclusion

**Useful bounded reasoning property, not demonstrated novelty.**

The project has stronger experimental controls around the composition boundary than a generic integration layer, but that methodological strength does not itself establish a new capability.

---

## 7. Candidate 6 — Identity and event identity across systems

### Candidate

The investigation considered whether preserving business-entity identity and event identity across independently owned systems could itself form the novel primitive.

### External overlap

Entity resolution across multiple independent sources is an established technical category. Current systems explicitly match, link, and enhance records across applications and data stores.

Current enterprise work also treats persistent identifiers and cross-reference architectures as mechanisms for linking entities across disconnected systems.

### Conclusion

**Not novel as an isolated capability.**

Identity integrity remains an important prerequisite for the project's reasoning experiments, but not a defensible standalone product novelty.

---

## 8. Candidate 7 — Cross-source conflict and provenance handling

### Candidate

The project tested whether evidence from multiple records could be composed or rejected based on identity, timing, relevance, authority, conflict, and provenance conditions.

### External overlap

Current cross-source evidence-adjudication research explicitly evaluates agreement, conflict, provenance, source quality, and whether a conclusion should be preserved or revised.

Current evidence-grounded decision systems also combine structured evidence constraints with counterfactual checks and explicit separation of supporting, contradicting, and missing evidence.

### Conclusion

**Not sufficiently differentiated.**

The project's controlled implementation may have useful engineering characteristics, but conflict/provenance-aware evidence handling is already an active capability area.

---

## 9. Candidate 8 — Novel methodology rather than novel capability

One distinction survives the audit more strongly than the capability candidates:

```text
independent authorship
+
frozen candidate
+
frozen evaluator
+
hidden oracle
+
paired base/variant execution
+
negative controls
+
identity/time/relevance quarantine
+
post-evaluation diagnostic isolation
```

This methodology has produced useful falsification evidence.

However, the methodology itself should not be marketed as a unique product capability without a separate novelty claim. Current metamorphic testing and counterfactual evaluation research already demonstrates that multi-execution behavioral relations, interventions, and independent evaluation can be used as rigorous testing mechanisms.

### Conclusion

**Research strength: demonstrated.**

**Standalone product novelty: not established.**

---

## 10. What the project actually demonstrated

The strongest defensible research contribution is methodological and empirical:

1. Controlled base/variant evaluation can reveal behavioral transition properties that ordinary single-output evaluation can miss.
2. Negative controls expose unsupported sensitivity.
3. Independent fixtures can expose a candidate's narrow pattern-domain coverage.
4. Cross-record composition can be tested conservatively under explicit identity, temporal, relevance, and conflict constraints.
5. Perfect pairwise preservation can be diagnostically degenerate when both systems fail to react to the intended evidence.
6. Candidate improvements that appear on one holdout may fail to replicate on an independently authored holdout.
7. Development-battery accuracy must not be interpreted as independent semantic generalization.

The last two points are particularly important: the independent replication showed equal 20% downstream decision fidelity for event-frame v1 and clause-local v2, and the post-evaluation coverage audit found that the frozen v2 extractor produced no EventFrames for the independent Gate-2 texts. The resulting 15/15 Gate-2 preservation score therefore cannot be interpreted as evidence of successful semantic generalization.

---

## 11. Novelty conclusion

The current evidence does **not** support the claim that the project has discovered a novel standalone AI-evaluation capability.

The following candidates should therefore remain rejected as novelty claims:

```text
context-driven decision integrity
cross-system semantic conformance
decision-transition witness
semantic/paraphrase invariance testing
cross-record semantic composition
cross-system entity/event identity
cross-source conflict/provenance handling
```

This is a research conclusion, not a statement that these capabilities are unimportant.

The project has demonstrated a substantial experimental methodology around these problems, but the capability boundary overlaps too heavily with existing literature and systems to justify calling any one of them novel on the evidence currently available.

---

## 12. Remaining research gap

No specific novel primitive has been identified.

The correct state is therefore:

```text
NOVEL PRIMITIVE:
UNPROVEN / UNDISCOVERED

Do not invent a replacement candidate merely to continue v0.3.
```

A future novelty claim must begin with a property that can be stated independently of the project's implementation and must survive a fresh literature/product audit before another fixture is created.

---

## 13. Product boundary

The validated v0.2 reasoning workflow remains the strongest established product boundary.

The research record does not currently justify representing v0.3 as a unique product capability.

External-system integration remains blocked by the existing acceptance boundary.

No extractor redesign, new H-series experiment, benchmark expansion, or new product capability is justified merely to manufacture a novelty claim.

---

## 14. Final research state

```text
Validated research methodology     YES
v0.2 baseline                      PROTECTED
v0.3 composition findings          BOUNDED / DEVELOPMENT-VALIDATED
v0.3 Gate 3                        PASS
v0.3 Gate 2                        NOT DEMONSTRATED
v0.3 novel capability              NOT ESTABLISHED
Independent provenance             SATISFIED
External integration               BLOCKED

Novelty program                    OPEN
Current implementation work        STOPPED
```

The next legitimate research action is **not another feature hypothesis**.

It is either:

```text
A. continue an explicitly open-ended novelty search
```

or

```text
B. close the novelty program and build the product around the
   validated v0.2 research boundary without making a novelty claim.
```

No conclusion above should be read as proof that no novel capability exists anywhere; it records what this project has and has not established under the research performed so far.
