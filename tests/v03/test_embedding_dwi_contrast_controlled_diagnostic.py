from __future__ import annotations

from test_embedding_target_confounder_enriched_v3 import (
    _all_development_examples,
)
from test_embedding_followup_nextstep_targeted_enrichment_v2 import (
    _encode,
)

from test_embedding_dwi_contrast_controlled_battery import CASES


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
        _, _, text, facts = example
        return text, facts

    if len(example) == 3:
        _, text, facts = example
        return text, facts

    if len(example) == 2:
        text, facts = example
        return text, facts

    raise AssertionError(
        f"Unexpected development example: {example!r}"
    )


def _development_examples():
    return [
        _unpack_example(example)
        for example in _all_development_examples()
    ]


def _mean(vectors):
    dim = len(vectors[0])

    return [
        sum(vector[i] for vector in vectors) / len(vectors)
        for i in range(dim)
    ]


def _score(embedding, positive_centroid, negative_centroid):
    return (
        _cosine(embedding, positive_centroid)
        - _cosine(embedding, negative_centroid)
    )


def _build_centroids(embeddings, labels):
    positive = [
        embeddings[i]
        for i, label in enumerate(labels)
        if label
    ]

    negative = [
        embeddings[i]
        for i, label in enumerate(labels)
        if not label
    ]

    assert positive
    assert negative

    return (
        _mean(positive),
        _mean(negative),
    )


def _calibrate_threshold():
    examples = _development_examples()

    texts = [text for text, _ in examples]
    labels = [
        DWI_FACT in facts
        for _, facts in examples
    ]

    embeddings = _encode(texts)

    loo_scores = []

    for holdout_index in range(len(embeddings)):
        train_embeddings = [
            embedding
            for i, embedding in enumerate(embeddings)
            if i != holdout_index
        ]

        train_labels = [
            label
            for i, label in enumerate(labels)
            if i != holdout_index
        ]

        positive_centroid, negative_centroid = (
            _build_centroids(
                train_embeddings,
                train_labels,
            )
        )

        loo_scores.append(
            _score(
                embeddings[holdout_index],
                positive_centroid,
                negative_centroid,
            )
        )

    candidates = sorted(
        set(
            [float(score) for score in loo_scores]
            + [0.0]
        )
    )

    best_threshold = None
    best_balanced_accuracy = -1.0

    for threshold in candidates:
        tp = tn = fp = fn = 0

        for score, expected in zip(
            loo_scores,
            labels,
        ):
            predicted = float(score) > threshold

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


def test_dwi_contrast_controlled_holdout():
    threshold, dev_balanced_accuracy = (
        _calibrate_threshold()
    )

    examples = _development_examples()

    development_texts = [
        text
        for text, _ in examples
    ]

    development_labels = [
        DWI_FACT in facts
        for _, facts in examples
    ]

    development_embeddings = _encode(
        development_texts
    )

    positive_centroid, negative_centroid = (
        _build_centroids(
            development_embeddings,
            development_labels,
        )
    )

    fresh_texts = []

    for _, current_item, different_item in CASES:
        fresh_texts.append(current_item)
        fresh_texts.append(different_item)

    fresh_embeddings = _encode(fresh_texts)

    print("\n=== CONTRAST-CONTROLLED DWI HOLDOUT ===")
    print(
        {
            "development_examples": len(examples),
            "dwi_positive": sum(development_labels),
            "dwi_negative": (
                len(development_labels)
                - sum(development_labels)
            ),
            "loo_threshold": round(
                threshold,
                6,
            ),
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
        current_score = _score(
            current_embedding,
            positive_centroid,
            negative_centroid,
        )

        different_score = _score(
            different_embedding,
            positive_centroid,
            negative_centroid,
        )

        current_predicted = (
            float(current_score) > threshold
        )

        different_predicted = (
            float(different_score) > threshold
        )

        current_ok = not current_predicted
        different_ok = different_predicted

        if current_ok:
            current_correct += 1

        if different_ok:
            different_correct += 1

        exact = current_ok and different_ok

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
                    current_predicted,
                "different_score": round(
                    float(different_score),
                    4,
                ),
                "different_predicted_dwi":
                    different_predicted,
                "pair_exact": exact,
            }
        )

    print("\n=== SUMMARY ===")
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