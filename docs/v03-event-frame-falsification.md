# v0.3 Event-Frame Candidate Falsification

## Status

Candidate evaluated and rejected as a demonstrated generalization improvement.

The candidate remains in the repository as an experimental artifact.

No further tuning of this candidate should use the frozen unseen holdout.

---

## 1. Research question

Can a dependency-free canonical event-frame representation reduce the
lexical dependence observed in the existing v0.3 normalized extractor?

The candidate was designed as:

```text
raw language
    ->
factual event frames
    ->
compatibility adapter
    ->
existing v0.3 reasoner
```

The candidate representation intentionally avoided benchmark answer labels.

---

## 2. Development-battery result

On the independently authored development battery:

```text
15 paraphrase pairs

candidate representation:
12/15 exact frame-set stable
80.0%

candidate end-to-end behavior:
15/15 stable
100.0%
```

These results were treated as development results only.

They were not considered sufficient evidence of generalization because the
candidate was iterated using that battery.

---

## 3. Unseen holdout

A separate unseen holdout was created after the candidate was frozen.

The holdout contained:

```text
5 semantic families
20 wording variants
15 paraphrase pairs
```

The candidate was not modified after holdout execution.

---

## 4. Holdout end-to-end result

Existing normalized extractor:

```text
11/15 behaviorally consistent
73.3%
```

Event-frame candidate:

```text
8/15 behaviorally consistent
53.3%
```

Difference:

```text
candidate - existing extractor
= -20.0 percentage points
```

Negative control:

```text
existing extractor: 3/3
candidate:          3/3
```

Therefore the candidate did not demonstrate improved unseen paraphrase
robustness.

---

## 5. Holdout factual-representation result

Using the independently authored holdout core-fact annotations:

```text
                        old extractor   candidate
complete fact sets          8/20           8/20
exact fact-set rate         40%            40%

mean fact precision         60%            60%
mean fact recall            50%            50%
```

The candidate therefore did not demonstrate a factual-representation
accuracy advantage over the existing extractor on the unseen holdout.

---

## 6. Failure interpretation

The candidate did improve some individual semantic expressions.

For example, it recovered facts that the old extractor missed in some
holdout variants.

However, those gains were offset by failures on other independently worded
variants.

Observed examples included:

```text
follow-up requests:
    candidate sometimes recognized a request that the old extractor missed,
    but missed other independently worded requests.

commercial rejection:
    candidate recognized some rejection formulations but missed several
    unseen formulations.

irrelevance:
    candidate recognized some explicit different-work-item expressions,
    but missed other natural formulations.

service completion / next step:
    candidate recovered completion reliably in some cases but did not
    consistently recover the next-step request.

supporting evidence:
    candidate recovered budget approval and procurement progression in
    several cases, while the old extractor sometimes recovered only part
    of the same situation.
```

The important result is not that one extractor is universally better.

It is that the event-frame representation, as implemented here, did not
produce a demonstrated generalization improvement on unseen language.

---

## 7. Scientific conclusion

The event-frame representation is not validated as the v0.3 redesign.

The experiment does NOT establish that event frames are intrinsically
inferior.

It establishes only:

> This particular dependency-free lexical event-frame implementation did
> not generalize better than the existing normalized extractor on the
> frozen unseen holdout.

The candidate should therefore not be optimized against the holdout.

---

## 8. What the experiment ruled out

The following hypothesis is not supported by the evidence:

```text
"Simply replacing boolean phrase matches with a canonical event-frame
schema will materially improve unseen paraphrase robustness."
```

The measured evidence does not justify that claim.

---

## 9. Next design requirement

The next representation experiment must introduce a materially different
source of semantic invariance rather than continuing to expand lexical
pattern coverage.

Any future candidate must be tested with:

```text
development battery
    ->
candidate freeze
    ->
unseen holdout
    ->
factual accuracy
    ->
behavioral consistency
    ->
negative-control resistance
```

The unseen holdout must remain untouched by subsequent candidate tuning.

---

## 10. Frozen evidence

The following results constitute the pre-redesign and failed-candidate
record:

```text
original normalized extractor
    development PBC: 53.3%
    unseen holdout PBC: 73.3%

event-frame candidate
    development PBC: 100.0%
    unseen holdout PBC: 53.3%

unseen holdout exact fact-set rate
    old:       40%
    candidate: 40%
```

The apparent 100% development result is therefore explicitly classified
as a development-battery result, not as evidence of generalization.
