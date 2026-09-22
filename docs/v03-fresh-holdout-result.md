# v0.3 Fresh Holdout Generalization Result

## Experiment

H5 — Clause-local decision-preservation hypothesis

## Evaluation Boundary

This evaluation used:

* the clause-local v2 implementation frozen at `05f8cbf`;
* the event-frame v1 comparator;
* the fresh holdout frozen at `1244c11`;
* the evaluator committed at `96c7701`.

No candidate implementation changes were made after the fresh holdout was frozen.

## Primary Metric

Pairwise downstream decision fidelity over 20 fresh-holdout variants.

A variant is counted as faithful only when the predefined downstream decision
tuple exactly matches the oracle-derived expected decision.

## Result

| Candidate       | Exact decisions | Total variants | Decision fidelity |
| --------------- | --------------: | -------------: | ----------------: |
| event-frame v1  |               6 |             20 |               30% |
| clause-local v2 |               7 |             20 |               35% |

Observed difference:

`clause-local v2 - event-frame v1 = +5 percentage points`

The difference corresponds to one additional exact decision out of 20.

## Per-Family Results

### FH1 — followup

* event-frame v1: 0/4
* clause-local v2: 1/4

### FH2 — supporting / approval

* event-frame v1: 1/4
* clause-local v2: 1/4

### FH3 — contradictory / rejection

* event-frame v1: 0/4
* clause-local v2: 1/4

### FH4 — irrelevant / different work item

* event-frame v1: 4/4
* clause-local v2: 4/4

### FH5 — service completion / next step

* event-frame v1: 1/4
* clause-local v2: 0/4

## Interpretation

The observed direction is consistent with H5 under the preregistered primary
metric: clause-local v2 produced higher exact decision fidelity on this fresh
holdout.

However, the observed margin is small: one net additional exact decision out
of 20 variants.

The paired results also show that the difference is not a uniform improvement:
clause-local v2 gains exact decisions in FH1 and FH3, while event-frame v1 has
one exact decision in FH5 that clause-local v2 does not reproduce.

Therefore this experiment provides **limited positive evidence consistent
with H5**, not a broad validation of clause-local v2 generalization.

No claim is made beyond the tested semantic families and surface constructions.

## Negative Control

FH4 contains explicitly different-work-item communications.

Both candidates preserved the expected primary-only decision for all four FH4
variants:

* event-frame v1: 4/4
* clause-local v2: 4/4

This provides evidence that the fresh evaluation did not expose a regression in
the tested different-work-item negative control.

## Determinism

The evaluator's deterministic oracle and candidate-evaluation checks passed.

## Experimental Integrity

The fresh holdout was frozen before candidate evaluation.

The holdout was not modified after evaluation began.

No candidate tuning or repair was performed in response to the fresh-holdout
results.

The earlier 0.85 clause-local result on the original holdout remains
post-hoc evidence and is not combined with this result.

## Conclusion

H5 is **directionally supported under the preregistered metric and this fresh
holdout**, but the result is too small to establish generalization broadly.

The next research step should therefore be an independent replication with a
new fresh holdout, rather than tuning clause-local v2 against the observed
failures.
