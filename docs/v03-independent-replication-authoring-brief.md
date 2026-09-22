# Independent Replication Holdout Authoring Brief

## Purpose

Create an evaluation fixture for a preregistered replication experiment comparing
two already-frozen text-to-semantics approaches.

The author must not inspect either implementation, prior candidate failures,
prior holdout texts, prior evaluation results, or diagnostic analyses.

## Required Structure

Create exactly 5 semantic families.

Each family must contain 4 independently written communication texts.

Within a family, the four texts must express the same intended semantic facts
while using different wording and sentence construction.

The texts must be written independently rather than by paraphrasing a supplied
prior example.

## Semantic Families

Family 1: a communication requesting a follow-up action related to the
existing work item.

Family 2: a communication explicitly confirming approval related to the
existing work item.

Family 3: a communication explicitly expressing rejection related to the
existing work item.

Family 4: a communication concerning a genuinely different work item or
initiative. This is the negative-control family.

Family 5: a communication confirming completion of the existing work item and
requesting a subsequent action.

## Oracle

For each family, record only semantic facts that are explicitly supported by
the text.

The oracle must distinguish:

* `true` — explicitly supported;
* `false` — explicitly contradicted or explicitly different-work-item where
  the schema requires that distinction;
* `null` — not established by the text.

Do not infer unstated facts.

The oracle must be fixed before either frozen candidate is evaluated.

## Construction Constraints

Use vocabulary and sentence structures chosen independently.

Do not consult:

* the previous H1–H5 holdout;
* previous clause-local failures;
* previous event-frame failures;
* previous candidate comparison results;
* repository diagnostics that expose candidate-specific weaknesses.

Do not attempt to make examples easier or harder for either candidate.

Do not tune the fixture after seeing any evaluation result.

## Metadata

For every case provide:

* unique `case_id`;
* primary interpretation label;
* primary decision strength;
* four texts;
* explicit oracle fields.

The complete fixture must be delivered as a JSON array conforming to the
repository's independent replication schema.

## Freeze Rule

Once the fixture and oracle are complete, the author must not modify them after
candidate evaluation begins.

The fixture should be supplied to the replication runner exactly as authored.

## Required Attestation

Alongside the fixture, provide a short statement confirming:

1. the author had no access to candidate-specific evaluation results;
2. the author did not copy or paraphrase the previous holdout;
3. the semantic oracle was fixed before candidate evaluation;
4. the fixture was not changed after evaluation began.
