# v0.3 Independent Replication Readiness Checkpoint

## Status

The frozen v0.3 acceptance state has been recorded.

The existing independent replication authoring protocol is already committed and frozen in:

`525cdfd docs: separate replication authoring brief from fixture`

The v0.3 final acceptance checkpoint is recorded before replication authoring.

## Replication Protocol

Independent replication will compare the two already-frozen text-to-semantics approaches:

- event-frame v1
- clause-local v2

The replication will use a genuinely fresh, independently authored holdout.

The existing authoring brief is the governing protocol:

`docs/v03-independent-replication-authoring-brief.md`

## Ordering Requirement

The required sequence is:

1. replication protocol committed;
2. independent author authors fresh fixture;
3. independent author fixes the semantic oracle;
4. independent attestation is supplied;
5. fixture schema and provenance are mechanically verified;
6. fixture and attestation are frozen;
7. frozen candidates are evaluated;
8. replication result is documented;
9. post-evaluation diagnostics, if any, remain separate from the replication result.

## Frozen Boundaries

The following must remain unchanged during replication authoring and evaluation:

- frozen v0.2 baseline;
- frozen v0.3 candidate;
- Gate-2 fixture;
- Gate-2 acceptance criterion;
- existing replication protocol.

No candidate tuning may occur against the fresh replication holdout.

## Current State

No fresh replication fixture has yet been evaluated.

No independent replication result exists yet.

This checkpoint authorizes the independent-authoring stage only.

## Repository Discipline

This checkpoint is local research history.

It must not be pushed to the remote repository before the replication evidence is complete unless explicitly decided later.

