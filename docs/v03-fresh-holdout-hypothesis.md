# v0.3 Fresh Holdout Generalization Hypothesis

## Purpose

Determine whether the frozen clause-local v2 extraction approach preserves
reasoner-relevant behavior on a genuinely fresh, independently authored
holdout.

This experiment exists to obtain clean generalization evidence after the
previous holdout-provenance limitation was identified.

## Research Question

When semantically equivalent communication variants are independently
authored after the candidate has been frozen, does clause-local v2 preserve
the same downstream reasoner decision more reliably than the earlier
event-frame v1 extractor?

## Hypothesis

**H5 — Clause-local decision-preservation hypothesis**

A clause-local extraction approach that assigns semantic event information
locally to clauses will produce greater pairwise downstream decision fidelity
than the earlier event-frame v1 representation when evaluated on a fresh
holdout that was authored independently after the candidate freeze.

The hypothesis concerns downstream decision preservation, not merely equality
of extracted representations.

## Candidate Status

The following implementations are frozen for this experiment:

* clause-local v2 candidate:
  `experiment.v03.clause_local_extractor_v2.ClauseLocalRelationalEventFrameExtractor`
* event-frame v1 comparator:
  the existing event-frame extraction path used by the prior holdout
  comparison.

Neither implementation may be modified after the fresh holdout is authored.

Any implementation change requires a new candidate freeze and a new
pre-registered evaluation.

## Fresh Holdout Construction Rules

The fresh holdout must be authored only after this hypothesis has been
committed.

The holdout authoring process must not use the old holdout texts as templates
or paraphrase sources.

The fresh examples must:

* be independently authored;
* cover multiple semantic families relevant to the reasoner;
* contain semantic-equivalence variants within each family;
* use vocabulary and surface constructions distinct from the prior holdout;
* include at least one negative-control family in which the communication
  concerns a different work item;
* have their semantic oracle specified before candidate evaluation;
* remain unchanged after evaluation begins.

No candidate-specific failure observed during the fresh holdout evaluation may
be used to rewrite the fresh holdout.

## Primary Metric

### Pairwise downstream decision fidelity

For each semantic family:

1. evaluate the primary/original text;
2. evaluate each independently authored variant;
3. compare the complete downstream reasoner decision tuple against the
   original.

A variant is counted as faithful only when the predefined decision tuple is
exactly equal to the original result.

The primary aggregate metric is:

`exactly faithful variant pairs / total variant pairs`

The metric is computed separately for clause-local v2 and event-frame v1.

## Secondary Measurements

The experiment will also record:

### Core-fact accuracy

Compare extracted explicit core facts against the pre-registered semantic
oracle.

Unknown or unobserved fields must not be silently converted into false.

### Negative-control resistance

For the different-work-item family, verify that the extraction/reasoning path
does not incorrectly preserve same-work-item semantics.

### Representation change versus decision change

Record whether a variant changes the extracted semantic representation and
whether that change propagates into a downstream decision change.

This is diagnostic only and must not be used to tune the frozen candidate.

### Determinism

Repeated evaluation of the identical input must produce identical results.

## Analysis Rules

The fresh holdout is an evaluation set, not a development set.

No threshold, lexical rule, parser rule, semantic mapping, feature definition,
or reasoner configuration may be changed after inspecting fresh-holdout
results.

No failed example may be individually repaired and re-evaluated as part of the
same experiment.

Any post-hoc investigation must be placed in a separate diagnostic experiment
and must not modify the frozen candidate or the fresh holdout.

## Interpretation

The experiment can support or fail to support H5 based on the pre-registered
measurements.

A higher clause-local v2 decision-fidelity measurement on the fresh holdout
would be evidence consistent with the hypothesis.

A lower or equal measurement would not support the hypothesis under the tested
conditions.

No conclusion about generalization outside the tested semantic families or
surface constructions may be made from this experiment alone.

## Required Provenance

The Git history must establish this sequence:

1. H5 pre-registration committed.
2. Candidate implementation frozen.
3. Fresh holdout independently authored.
4. Fresh holdout oracle fixed.
5. Evaluation executed without candidate modification.
6. Results documented.
7. Any diagnostics separated from the evaluation result.

The fresh holdout and its oracle become immutable after step 4.

## Existing Evidence Boundary

The earlier clause-local v2 result on the original holdout is retained only as
post-hoc evidence because its provenance does not establish unbiased
candidate construction.

That earlier result must not be combined with the fresh-holdout result into a
single metric.

The fresh-holdout result is the designated evidence for H5.
