# UI Information Architecture v1

## 1. Product navigation

The primary navigation remains intentionally small:

- Overview
- Evaluations
- Integrations
- Reports

Advanced research and diagnostic information is progressively disclosed rather than placed in the primary navigation.

## 2. Homepage

The homepage communicates the product in business language.

Primary message:

> Does additional context actually change a decision?

Primary actions:

- Start an evaluation
- Integrate

The homepage should not require users to understand fixtures, extractors, reasoners, or evaluation internals.

## 3. Evaluation creation

The creation flow should answer only the information necessary to begin an evaluation.

Initial flow:

1. Choose the evaluation type.
2. Select or provide the primary input.
3. Select or provide the secondary context.
4. Review the evaluation scope.
5. Start the evaluation.

Advanced configuration is hidden behind an explicit advanced-control area.

## 4. Evaluation run state

The run screen should communicate:

- what is being evaluated;
- current progress;
- whether the evaluation is still running;
- whether an input or system error occurred.

The interface should not expose implementation logs by default.

A user can access technical diagnostics through an advanced view.

## 5. Result screen

The result screen is the primary product experience.

It should present:

- overall result;
- expected outcome;
- observed outcome;
- evidence summary;
- identity status;
- temporal status;
- context relevance status;
- provenance status.

Example high-level layout:

```text
RESULT

Overall result
20 / 20 cases passed

What happened?
What changed?
Why?
What evidence supports the result?

[ Inspect evidence ]
[ Explore cases ]
[ Export report ]
```

A PASS or FAIL summary must never be the only information available to the user.

## 6. Evidence inspection

Evidence inspection must show the chain from input to result.

The user should be able to inspect:

1. Primary information.
2. Secondary information.
3. Identity matching.
4. Temporal validity.
5. Context relevance.
6. Evidence selected for the result.
7. Resulting interpretation.

Evidence should be presented in business-readable form first, with technical detail available progressively.

## 7. Case explorer

The case explorer provides a deeper view of individual evaluation cases.

Each case should show:

- case identifier;
- category or family;
- expected behavior;
- observed behavior;
- result state;
- relevant evidence;
- failed or passed checks.

The user should be able to filter by result state and evaluation dimension.

The case explorer is where the research-oriented detail becomes visible without making it part of the basic workflow.

## 8. Reports

Reports should provide a stable shareable representation of an evaluation.

A report should contain:

- evaluation identifier;
- evaluation version;
- date/time;
- overall result;
- summary metrics where validated;
- evidence summary;
- case-level results;
- provenance;
- limitations.

Export formats should initially prioritize a human-readable report.

Machine-readable export can be added after the result contract is stable.

## 9. Integrations

The Integrations area should present the second product path clearly.

It should contain:

- API overview;
- authentication guidance;
- request examples;
- response examples;
- integration status;
- SDK information when available.

The same result model used in the Workspace must be represented by the API.

The integration UI should not imply capabilities that are not established by current evidence.

Private or self-hosted deployment belongs under deployment/integration configuration rather than becoming a third primary product choice.

## 10. Empty, loading, and error states

Every primary screen must define explicit states for:

- no evaluations yet;
- evaluation loading;
- evaluation completed;
- invalid input;
- unavailable data;
- execution failure;
- partial or requires-review results.

Errors should explain what the user can do next without exposing implementation details unless technical diagnostics are requested.

## 11. Progressive disclosure

The interface uses three levels of detail.

Level 1 — Simple

- result;
- short explanation;
- next action.

Level 2 — Evidence

- evidence;
- identity checks;
- temporal checks;
- context relevance;
- case details.

Level 3 — Research / technical

- fixtures;
- invariants;
- provenance metadata;
- diagnostic traces;
- experimental implementation details.

Level 3 must never be required for ordinary evaluation use.

## 12. Desktop and mobile behavior

Desktop is the primary environment for detailed evaluation and case inspection.

Mobile must preserve the primary flow:

Start evaluation → Run → Result → Evidence.

Complex tables should become stacked cards or horizontally scrollable detail sections on narrow screens.

Critical actions must remain accessible without requiring desktop-only interactions.

## 13. Shared UI and API result model

The Workspace and API must consume the same conceptual result object.

Conceptually:

```text
                    Evaluation Result
                           |
              +------------+------------+
              |                         |
           Web UI                    API / SDK
```

Neither interface may independently redefine result semantics.

## 14. First-version non-goals

The first UI version does not need:

- multi-tenant administration;
- billing;
- complex team permissions;
- arbitrary workflow builders;
- advanced analytics dashboards;
- generalized AI chat;
- production automation controls.

These are separate product decisions and should not enter the first implementation accidentally.

## 15. First UI milestone

The first usable web application consists of:

```text
Home
  ↓
New Evaluation
  ↓
Run
  ↓
Result
  ├── Evidence
  ├── Case Explorer
  └── Export Report

Integrations
  ├── API
  └── Integration Guide
```

The implementation must remain a thin interface over the existing product core.
