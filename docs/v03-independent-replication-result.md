# v0.3 Independent Replication Result

## Experiment

Independent replication of the frozen event-frame v1 and clause-local v2 text-to-semantics approaches.

The replication used a fresh independently authored holdout frozen before candidate evaluation.

## Frozen Inputs

Replication fixture:

`tests/v03/independent_replication/fixture.json`

Replication attestation:

`tests/v03/independent_replication/attestation.json`

The provenance verifier reported:

- `independent_verified`
- 5 cases
- 20 variants
- candidate evaluation was false during provenance verification

The fixture and attestation were frozen before evaluation.

## Primary Result

| Candidate | Exact decisions | Total variants | Decision fidelity |
|---|---:|---:|---:|
| event-frame v1 | 4 | 20 | 20% |
| clause-local v2 | 4 | 20 | 20% |

Observed difference:

`clause-local v2 - event-frame v1 = 0 percentage points`

## Per-Family Results

| Family | event-frame v1 | clause-local v2 |
|---|---:|---:|
| IRH-F1 follow-up | 0/4 | 0/4 |
| IRH-F2 approval | 0/4 | 0/4 |
| IRH-F3 rejection | 0/4 | 0/4 |
| IRH-F4 different work item | 4/4 | 4/4 |
| IRH-F5 completion + subsequent action | 0/4 | 0/4 |

## Interpretation

The preregistered H5 hypothesis predicted that clause-local v2 would produce greater pairwise downstream decision fidelity than event-frame v1 on a fresh independent holdout.

The replication produced equal fidelity:

`20% vs 20%`

Therefore the replication does **not support H5** under these tested conditions.

The four substantive semantic families produced no exact candidate decisions for either implementation.

The different-work-item negative-control family was preserved by both candidates at 4/4.

This pattern is consistent with the previously observed coverage boundary: both candidates can preserve primary decisions when secondary evidence is not recognized, while failing to convert the independently authored substantive communications into the semantic evidence required for the expected downstream effect.

## Relationship to Earlier H5 Result

The earlier fresh-holdout experiment produced:

- event-frame v1: 30%
- clause-local v2: 35%

That earlier result was already characterized as limited positive evidence rather than broad validation.

The independent replication did not reproduce that advantage.

The two results therefore must not be averaged or combined into a single metric.

The appropriate conclusion is:

> The earlier H5 direction was not replicated on the new independent holdout.

## Scope

This result does not justify:

- modifying the frozen v0.3 candidate;
- modifying the replication fixture;
- changing the Gate-2 criterion;
- declaring either extraction approach generally incapable of semantic reasoning;
- beginning an unrestricted NLP redesign.

It establishes only the tested replication result and its evidence boundary.

## Research Conclusion

H5 is **not supported by the independent replication**.

The evidence now indicates that the demonstrated advantage of clause-local v2 over event-frame v1 is not robust across the tested independent holdouts.

The current strongest evidence is:

> Clause-local v2 showed a small advantage on the first fresh holdout, but that advantage was not reproduced on independent replication; both frozen approaches achieved 20% decision fidelity on the replication holdout.

The frozen candidates remain unchanged.

Any next research hypothesis must be separately preregistered and must not modify the completed H5 evidence.
