# Product Contract v1

## 1. Product purpose

Cross-System Context Test evaluates whether additional business context changes a decision in the direction supported by controlled evidence.

The product provides two interfaces over one shared evaluation core:

- Workspace: a professional, low-complexity web experience for people who want to run and inspect evaluations without programming.
- Integration: an API/SDK interface for embedding evaluation capabilities into an existing application or workflow.

A future private/self-hosted deployment is a deployment option, not a separate product surface.

## 2. Product promise

The product helps a user answer:

> Does the additional context actually justify changing, strengthening, weakening, or preserving the existing interpretation?

The product must show the evidence supporting the result and must distinguish demonstrated behavior from experimental behavior.

## 3. Workspace

The primary user flow is:

1. Start an evaluation.
2. Select or provide the evaluation input.
3. Run the evaluation.
4. See the result.
5. Inspect why the result was produced.
6. Inspect individual cases when needed.
7. Export/share the evaluation report.

The default interface should hide research implementation details.

The default vocabulary should be business-facing rather than implementation-facing.

Research concepts such as fixtures, oracles, extractors, reasoners, metamorphic cases, and internal invariants belong in advanced/research views, not the primary workflow.

## 4. Workspace information architecture

Top-level navigation should remain small:

- Overview
- Evaluations
- Integrations
- Reports

Research/developer diagnostics may exist as an advanced area but must not dominate the normal user experience.

## 5. Evaluation result

Every evaluation must produce a structured result containing at least:

- evaluation identifier
- evaluation version
- overall result
- expected outcome
- observed outcome
- evidence
- identity validity
- temporal validity
- context relevance
- provenance
- reproducibility information

A result must never be reduced to a single unexplained PASS/FAIL indicator in the product UI.

PASS/FAIL may be the summary, but the user must be able to inspect the underlying evidence and checks.

## 6. Integration interface

The integration surface must expose the same semantic result model used by the Workspace.

The initial API contract should support:

- submit evaluation
- retrieve evaluation status
- retrieve evaluation result
- retrieve evidence

The API must not expose a different interpretation of a result from the Workspace.

The API must not claim capabilities that have not been demonstrated by the research evidence.

## 7. Core result states

The product should distinguish at least:

- supported
- weakened
- strengthened
- preserved
- requires_review
- invalid_input
- unavailable

These are result states, not quality scores.

The product must not manufacture confidence scores unless a validated confidence model exists.

## 8. Evidence model

Evidence shown to the user must answer:

1. What primary information was evaluated?
2. What secondary information was considered?
3. Why was the secondary information eligible?
4. Which identity checks passed or failed?
5. Which temporal checks passed or failed?
6. What interpretation changed or stayed the same?
7. What evidence supports that result?

## 9. Provenance

Every evaluation result should remain traceable to:

- the evaluation version
- the input
- the evaluation configuration
- the evidence considered
- the resulting decision

The system must preserve reproducibility information for results that are presented as validated.

## 10. Trust boundaries

The product must clearly distinguish three states of knowledge:

- Demonstrated: supported by the frozen evaluation evidence.
- Experimental: implemented or tested, but not established as a broad capability.
- Not demonstrated: not supported by current evidence.

The UI must never present experimental semantic extraction as general-purpose understanding.

## 11. Current release boundary

The first public product exposes the validated v0.2 controlled experiment.

The v0.3 semantic-extraction research remains outside the public product capability until independently supported.

## 12. Non-goals

The initial product does not claim:

- universal natural-language understanding
- arbitrary production-system integration
- universal identity resolution
- causal inference
- production decision automation
- arbitrary real-world dataset validity

## 13. Product architecture

There is one core evaluation model.

Workspace, API, and future SDKs are interfaces over that model.

They must not implement separate evaluation semantics.

Conceptually:

Workspace ----\
                >---- Shared Product Core ---- Research boundary
API -----------/

## 14. UI design principles

The normal user should need to understand the task, not the implementation.

The interface should prioritize:

- clarity
- evidence
- traceability
- low cognitive load
- progressive disclosure

Advanced detail is available when needed, but never forced on the user.

## 15. First UI milestone

The first web application must support:

- landing/dashboard
- create evaluation
- run evaluation
- evaluation result
- case explorer
- evidence inspection
- report export
- Integrations entry point

The first implementation should remain a thin interface over the existing validated evaluation core.
