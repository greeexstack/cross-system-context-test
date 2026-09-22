# v0.3 Holdout Provenance Audit

## Purpose

Record whether the clause-local v2 holdout result can be treated as an unbiased
generalization measurement.

## Chronology

- `124d65c` — 2026-09-19 00:56 — `test: record event-frame holdout falsification`
  - Introduced `tests/v03/test_event_frame_holdout.py`.
  - This commit contains the 5-family unseen holdout (`H1`–`H5`).

- `05f8cbf` — 2026-09-19 01:45 — `test: freeze clause-local extraction candidate`
  - Introduced the clause-local extraction implementations and their
    development/evaluation tests.
  - The commit is a descendant of `124d65c`, so the holdout already existed
    in repository history when the clause-local candidate was introduced.

- `41ccba5` — 2026-09-19 15:06 — `test: compare clause-local extraction on unseen holdout`
  - Added the holdout comparison harness.

- `81ca1cc` — 2026-09-19 15:09 — `test: measure holdout decision fidelity`
  - Added the holdout decision-fidelity measurement.

- `b4f9f7d` — 2026-09-19 15:15 — `test: falsify clause-local construction generalization`
  - Added a later construction-focused battery.

## Important provenance observation

The `05f8cbf` freeze commit also contains
`tests/v03/test_holdout_counterfactual_field_repair.py`.

That analysis directly imports the existing holdout and measures the prior
candidate extraction path against it. It is therefore evidence that holdout
analysis was already part of the research context at the time the clause-local
candidate was committed.

The clause-local development battery itself does not import the holdout and
states that it uses different vocabulary from earlier holdout/development
batteries.

## Classification

The existing clause-local v2 holdout result must **not** be treated as a
clean, pre-registered, holdout-independent generalization result.

Reason:

Repository ancestry proves that the holdout existed before the clause-local
candidate freeze, while the freeze commit also contains explicit holdout
counterfactual analysis. The available history does not establish that
clause-local v2 was designed without knowledge of that holdout.

This is an evaluation-provenance limitation, not evidence that the clause-local
candidate itself is invalid.

## Treatment of the previously measured result

The previously observed clause-local v2 decision fidelity of 0.85 versus 0.55
for event-frame v1 is retained as a **post-hoc evaluation observation only**.

It must not be used as unbiased evidence of generalization or as the basis for
claiming that clause-local v2 has been validated on an unseen holdout.

No tuning or candidate modification should be performed against that holdout.

## Required next experiment

Use a genuinely fresh holdout created after the candidate is frozen.

The new holdout must:

1. be authored independently of the candidate implementation,
2. have its semantic oracle fixed before candidate evaluation,
3. remain inaccessible to candidate development/tuning,
4. evaluate the frozen clause-local v2 implementation without modification,
5. include behavioral fidelity and negative-control measurements,
6. preserve the development → freeze → fresh holdout sequence in Git history.

Only that fresh evaluation should be considered for a clean generalization claim.