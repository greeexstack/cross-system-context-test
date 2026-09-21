# v0.3 Representation Factuality Experiment — Result

## Status

H4 is not supported under the tested development annotations.

The experiment does not show that representation drift is generally
equivalent to factual semantic error.

The unseen holdout remains frozen and was not used.

---

## 1. Experiment

The normalized extractor was evaluated against the explicitly annotated
semantic fields in `test_extractor_paraphrases.py`.

Only fields explicitly assigned `True` or `False` were evaluated.

`None` was treated as unspecified and was not scored.

---

## 2. Aggregate result

Explicit field decisions:

```
14
```

Matching decisions:

```
13
```

Factual field accuracy:

```
13 / 14 = 92.86%
```

---

## 3. Pair-level result

### F01-D1

Original:

```
all explicitly annotated fields correct
```

Paraphrase:

```
all explicitly annotated fields correct
```

No factual disagreement observed.

### F02-D1

Original:

```
all explicitly annotated fields correct
```

Paraphrase:

```
all explicitly annotated fields correct
```

No factual disagreement observed.

### F03-D1

Original:

```
all explicitly annotated fields correct
```

Paraphrase:

```
all explicitly annotated fields correct
```

No factual disagreement observed.

### F04-D1

Original:

```
all explicitly annotated fields correct
```

Paraphrase:

```
all explicitly annotated fields correct
```

No factual disagreement observed.

### F10-D1

Original:

```
`requests_next_step` was not recovered.
```

Paraphrase:

```
`requests_next_step` was recovered correctly.
```

The representation change therefore moved the paraphrase toward the explicit
expected fact rather than introducing a factual error.

---

## 4. Important distinction

The experiment demonstrates:

```
representation drift
    !=
factual error
```

cannot be assumed.

A representation can differ across wording variants while remaining correct
on the explicitly evaluated semantic fields.

---

## 5. Relationship to H3

The previous representation-restoration experiment showed that all seven
observed development behavioral-change cases were representation-mediated.

The present experiment shows that, under the explicit extractor-specific
annotations, 13 of 14 evaluated field decisions were factually correct.

These findings are compatible.

They indicate that a representation difference can influence downstream
behavior even when the changed representation is not demonstrably factually
wrong under the current annotation set.

---

## 6. What this experiment does NOT establish

It does not establish:

* that every representation difference is semantically benign;
* that unannotated fields are irrelevant;
* that the semantic schema is optimal;
* that the extractor is free of factual errors outside the evaluated fields;
* that the result generalizes to the unseen holdout.

Only explicitly annotated fields were evaluated.

---

## 7. Invalid measurement discarded

An earlier version of this experiment incorrectly compared the normalized
extractor against reasoner-oriented fixture fields that the extractor
contract does not assert positively.

In particular, `concerns_same_work_item=True` was incorrectly treated as a
required extractor output.

The normalized extractor represents this field as:

```
False
or
None
```

where `None` means that same-work-item status was not established.

That earlier measurement is therefore invalid and must not be used as
research evidence.

The corrected experiment uses the extractor-specific annotations from
`test_extractor_paraphrases.py`.

---

## 8. Research conclusion

H4 is not supported under the tested development conditions.

The evidence does not justify interpreting representation drift itself as
evidence of factual extraction failure.

The remaining question is why some representation differences alter
downstream behavior even when the explicitly evaluated facts remain correct.

That question requires another controlled experiment.

---

## 9. Frozen-data policy

The unseen holdout remains untouched.

No extractor tuning was performed using the holdout.

No production code was modified.
