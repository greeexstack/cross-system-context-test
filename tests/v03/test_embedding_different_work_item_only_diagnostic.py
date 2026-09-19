from __future__ import annotations

from test_embedding_target_confounder_enriched_v3 import (
    _all_development_examples,
)
from test_embedding_followup_nextstep_targeted_enrichment_v2 import (
    _encode,
)

from test_embedding_different_work_item_only_battery import CASES


DWI_FACT = "different_work_item"


def _cosine(a, b):
    denom = (sum(x * x for x in a) ** 0.5) * (
        sum(x * x for x in b) ** 0.5
    )

    if denom == 0:
        return 0.0

    return sum(x * y for x, y in zip(a, b)) / denom


def _unpack_example(example):
    if len(example) == 4:
        _, _, text, expected_facts = example
        return text, expected_facts

    if len(example) == 3:
        _, text, expected_facts = example
        return text, expected_facts

    if len(example) == 2:
        text, expected_facts = example
        return text, expected_facts

    raise AssertionError(
        f"Unexpected development-example structure: {example!r}"
    )


def _development_examples():
    return [
        _unpack_example(example)
        for example in _all_development_examples()
    ]


def _build_loo_score(
    embeddings,
    labels,
    holdout_index,
):
    positive = [
        embeddings[i]
        for i in range(len(embeddings))
        if i != holdout_index and labels[i]
    ]

    negative = [
        embeddings[i]
        for i in range(len(embeddings))
        if i != holdout_index and not labels[i]
    ]

    holdout = embeddings[holdout_index]

    positive_similarity = max(
        _cosine(holdout, vector)
        for vector in positive
    )

    negative_similarity = max(
        _cosine(holdout, vector)
        for vector in negative
    )

    return positive_similarity - negative_similarity


def _calibrate_threshold():
    examples = _development_examples()

    texts = [text for text, _ in examples]

    embeddings = _encode(texts)

    labels = [
        DWI_FACT in facts
        for _, facts in examples
    ]

    loo_scores = [
        float(
            _build_loo_score(
                embeddings,
                labels,
                i,
            )
        )
        for i in range(len(embeddings))
    ]

    candidates = sorted(
        set(loo_scores + [0.0])
    )

    best_threshold = None
    best_balanced_accuracy = -1.0

    for threshold in candidates:
        tp = tn = fp = fn = 0

        for score, expected in zip(
            loo_scores,
            labels,
        ):
            predicted = score > threshold

            if expected and predicted:
                tp += 1
            elif expected and not predicted:
                fn += 1
            elif not expected and not predicted:
                tn += 1
            else:
                fp += 1

        sensitivity = (
            tp / (tp + fn)
            if (tp + fn)
            else 0.0
        )

        specificity = (
            tn / (tn + fp)
            if (tn + fp)
            else 0.0
        )

        balanced_accuracy = (
            sensitivity + specificity
        ) / 2.0

        if balanced_accuracy > best_balanced_accuracy:
            best_balanced_accuracy = balanced_accuracy
            best_threshold = threshold

    return (
        float(best_threshold),
        float(best_balanced_accuracy),
    )


def _fresh_score(
    embedding,
    positive_examples,
    negative_examples,
):
    positive_similarity = max(
        _cosine(embedding, vector)
        for vector in positive_examples
    )

    negative_similarity = max(
        _cosine(embedding, vector)
        for vector in negative_examples
    )

    return (
        positive_similarity
        - negative_similarity
    )


def test_dwi_nearest_example_minimal_pairs():
    threshold, dev_balanced_accuracy = (
        _calibrate_threshold()
    )

    examples = _development_examples()

    texts = [text for text, _ in examples]

    embeddings = _encode(texts)

    labels = [
        DWI_FACT in facts
        for _, facts in examples
    ]

    positive_examples = [
        embeddings[i]
        for i, label in enumerate(labels)
        if label
    ]

    negative_examples = [
        embeddings[i]
        for i, label in enumerate(labels)
        if not label
    ]

    fresh_texts = []

    for _, current_item, different_item in CASES:
        fresh_texts.append(current_item)
        fresh_texts.append(different_item)

    fresh_embeddings = _encode(fresh_texts)

    print("\n=== NEAREST-EXAMPLE DWI MODEL ===")

    print(
        {
            "development_examples": len(examples),
            "dwi_positive": len(positive_examples),
            "dwi_negative": len(negative_examples),
            "loo_threshold": round(threshold, 6),
            "loo_balanced_accuracy": round(
                dev_balanced_accuracy,
                4,
            ),
        }
    )

    pair_exact = 0
    current_correct = 0
    different_correct = 0

    for (
        pair_id,
        current_item,
        different_item,
    ), current_embedding, different_embedding in zip(
        CASES,
        fresh_embeddings[::2],
        fresh_embeddings[1::2],
    ):
        current_score = _fresh_score(
            current_embedding,
            positive_examples,
            negative_examples,
        )

        different_score = _fresh_score(
            different_embedding,
            positive_examples,
            negative_examples,
        )

        current_predicted_dwi = (
            current_score > threshold
        )

        different_predicted_dwi = (
            different_score > threshold
        )

        current_ok = not current_predicted_dwi
        different_ok = different_predicted_dwi

        if current_ok:
            current_correct += 1

        if different_ok:
            different_correct += 1

        exact = (
            current_ok
            and different_ok
        )

        if exact:
            pair_exact += 1

        print(
            {
                "pair": pair_id,
                "current_score": round(
                    float(current_score),
                    4,
                ),
                "current_predicted_dwi":
                    current_predicted_dwi,
                "different_score": round(
                    float(different_score),
                    4,
                ),
                "different_predicted_dwi":
                    different_predicted_dwi,
                "pair_exact": exact,
            }
        )

    print("\n=== NEAREST-EXAMPLE SUMMARY ===")

    print(
        {
            "pair_exact": pair_exact,
            "pair_total": len(CASES),
            "pair_accuracy": round(
                pair_exact / len(CASES),
                4,
            ),
            "current_item_correct":
                current_correct,
            "different_item_correct":
                different_correct,
        }
    )

    assert len(CASES) == 8