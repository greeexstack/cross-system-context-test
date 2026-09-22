# v0.3 Fresh Holdout Provenance Correction

## Purpose

Correct the provenance classification of the holdout used for the H5
evaluation recorded in `docs/v03-fresh-holdout-result.md`.

## Finding

The holdout committed at `1244c11` was created after the H5 hypothesis was
pre-registered and after the clause-local v2 candidate had been frozen.

However, the holdout text was authored within the same research process after
the researchers had already observed earlier holdout results and failure
patterns.

Although the fresh texts were new, used different wording, and were frozen
before candidate evaluation, their construction was not independently blinded
from prior candidate evidence.

## Consequence

The evaluation result:

* event-frame v1: 6/20 = 30%
* clause-local v2: 7/20 = 35%

remains a valid measurement of the two frozen implementations on that specific
fixed fixture.

It must **not** be treated as an unbiased or independently authored
generalization result.

The previously recorded conclusion that H5 received positive generalization
evidence is therefore withdrawn.

The result remains available as a post-hoc prospective evaluation observation.

## What Remains Valid

The following facts remain valid:

1. The clause-local v2 implementation was unchanged during evaluation.
2. The holdout was frozen before the evaluation was executed.
3. The oracle was fixed before evaluation.
4. No candidate tuning was performed after observing the evaluation.
5. The evaluator was deterministic.
6. The measured difference was +5 percentage points, corresponding to one
   additional exact decision out of 20.

These facts establish execution integrity, but they do not establish
independent holdout construction.

## Required Evidence for Clean Replication

A future replication must separate holdout authoring from candidate
development.

The author of the holdout must not have access to:

* candidate-specific failure cases;
* prior holdout failure locations;
* candidate comparison results;
* post-hoc diagnostic analyses that identify useful constructions.

The semantic family matrix, oracle, and text variants must be fixed before the
candidate is evaluated.

The candidate must remain frozen throughout the replication.

Only that independently authored replication should be used for a clean
generalization claim.

## Research Status

H5 is therefore **not established by the current fresh-holdout experiment**.

The current evidence should be classified as:

`prospective evaluation, non-independent holdout construction`

and not:

`clean generalization validation`.
