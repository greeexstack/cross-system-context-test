from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Tuple

import numpy as np

from test_clause_local_development_battery import DEVELOPMENT_BATTERY
from test_embedding_semantic_separation import MODEL, MODEL_NAME
from test_event_frame_holdout import HOLDOUT


DEV_TO_SEMANTIC = {
    "D1-followup": "followup",
    "D2-supporting": "approval",
    "D3-contradictory": "rejection",
    "D4-irrelevant": "different_work_item",
    "D5-service-next-step": "next_step",
}

HOLDOUT_TO_SEMANTIC = {
    "H1-followup": "followup",
    "H2-supporting": "approval",
    "H3-contradictory": "rejection",
    "H4-irrelevant": "different_work_item",
    "H5-service-next-step": "next_step",
}


def _encode(texts: List[str]) -> np.ndarray:
    return MODEL.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )


def _variant_text(variant) -> str:
    if isinstance(variant, (tuple, list)):
        return str(variant[0])
    return str(variant)


def _build_development_centroids() -> Dict[str, np.ndarray]:
    grouped: Dict[str, List[str]] = {
        semantic_label: []
        for semantic_label in DEV_TO_SEMANTIC.values()
    }

    for family_id, _primary_state, variants in DEVELOPMENT_BATTERY:
        semantic_label = DEV_TO_SEMANTIC[family_id]

        for variant in variants:
            grouped[semantic_label].append(_variant_text(variant))

    centroids: Dict[str, np.ndarray] = {}

    for semantic_label, texts in grouped.items():
        embeddings = _encode(texts)

        centroid = np.mean(embeddings, axis=0)
        norm = float(np.linalg.norm(centroid))

        if norm == 0.0:
            raise ValueError(
                f"Zero centroid for semantic label {semantic_label!r}"
            )

        centroids[semantic_label] = centroid / norm

    return centroids


def _nearest_centroid(
    embedding: np.ndarray,
    centroids: Dict[str, np.ndarray],
) -> Tuple[str, Dict[str, float]]:
    similarities = {
        label: float(embedding @ centroid)
        for label, centroid in centroids.items()
    }

    predicted = max(similarities, key=similarities.get)

    return predicted, similarities


def test_development_centroids_are_built_only_from_development_data() -> None:
    centroids = _build_development_centroids()

    assert set(centroids) == {
        "followup",
        "approval",
        "rejection",
        "different_work_item",
        "next_step",
    }

    for label, centroid in centroids.items():
        assert centroid.shape == (384,), label
        assert np.isclose(np.linalg.norm(centroid), 1.0, atol=1e-6), label

    print("\n=== DEVELOPMENT-TRAINED EMBEDDING CENTROIDS ===")
    print(f"model={MODEL_NAME}")

    for family_id, semantic_label in DEV_TO_SEMANTIC.items():
        texts = []

        for current_family_id, _primary_state, variants in DEVELOPMENT_BATTERY:
            if current_family_id != family_id:
                continue

            texts.extend(_variant_text(variant) for variant in variants)

        print(
            {
                "development_family": family_id,
                "semantic_label": semantic_label,
                "training_examples": len(texts),
            }
        )


def test_development_centroid_leave_one_out_training_sanity() -> None:
    print("\n=== DEVELOPMENT LEAVE-ONE-OUT CENTROID SANITY ===")

    grouped: Dict[str, List[str]] = {
        semantic_label: []
        for semantic_label in DEV_TO_SEMANTIC.values()
    }

    for family_id, _primary_state, variants in DEVELOPMENT_BATTERY:
        semantic_label = DEV_TO_SEMANTIC[family_id]
        grouped[semantic_label].extend(
            _variant_text(variant)
            for variant in variants
        )

    total = 0
    correct = 0

    for semantic_label, texts in grouped.items():
        embeddings = _encode(texts)

        for index, embedding in enumerate(embeddings):
            centroids: Dict[str, np.ndarray] = {}

            for other_label, other_texts in grouped.items():
                other_embeddings = _encode(other_texts)

                if other_label == semantic_label:
                    remaining = np.delete(
                        other_embeddings,
                        index,
                        axis=0,
                    )
                else:
                    remaining = other_embeddings

                centroid = np.mean(remaining, axis=0)
                centroid = centroid / np.linalg.norm(centroid)
                centroids[other_label] = centroid

            predicted, _ = _nearest_centroid(embedding, centroids)

            total += 1
            if predicted == semantic_label:
                correct += 1

    accuracy = correct / total

    print(
        {
            "total_development_variants": total,
            "leave_one_out_correct": correct,
            "accuracy": accuracy,
        }
    )

    assert total == 20


def test_development_centroids_on_unseen_holdout() -> None:
    centroids = _build_development_centroids()

    print("\n=== DEVELOPMENT-TRAINED CENTROIDS ON UNSEEN HOLDOUT ===")
    print(f"model={MODEL_NAME}")

    total = 0
    correct = 0

    family_totals: Dict[str, int] = {
        semantic_label: 0
        for semantic_label in HOLDOUT_TO_SEMANTIC.values()
    }

    family_correct: Dict[str, int] = {
        semantic_label: 0
        for semantic_label in HOLDOUT_TO_SEMANTIC.values()
    }

    for family_id, _primary, texts, _expected_facts in HOLDOUT:
        expected_label = HOLDOUT_TO_SEMANTIC[family_id]

        for variant_index, text in enumerate(texts):
            embedding = _encode([text])[0]

            predicted, similarities = _nearest_centroid(
                embedding,
                centroids,
            )

            is_correct = predicted == expected_label

            total += 1
            family_totals[expected_label] += 1

            if is_correct:
                correct += 1
                family_correct[expected_label] += 1

            print(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "predicted": predicted,
                    "expected": expected_label,
                    "correct": is_correct,
                    "similarities": {
                        label: round(score, 4)
                        for label, score in similarities.items()
                    },
                    "text": text,
                }
            )

    accuracy = correct / total

    print(
        {
            "model": MODEL_NAME,
            "training_source": "development battery only",
            "evaluation_source": "unseen holdout only",
            "total_holdout_variants": total,
            "correct": correct,
            "accuracy": accuracy,
            "fixed_anchor_baseline": "14/20 = 70.0%",
        }
    )

    print("\n=== UNSEEN HOLDOUT ACCURACY BY FAMILY ===")

    for semantic_label in (
        "followup",
        "approval",
        "rejection",
        "different_work_item",
        "next_step",
    ):
        family_accuracy = (
            family_correct[semantic_label]
            / family_totals[semantic_label]
        )

        print(
            {
                "semantic_label": semantic_label,
                "correct": family_correct[semantic_label],
                "total": family_totals[semantic_label],
                "accuracy": family_accuracy,
            }
        )


def test_development_centroid_holdout_negative_control() -> None:
    centroids = _build_development_centroids()

    print("\n=== DEVELOPMENT-CENTROID HOLDOUT NEGATIVE CONTROL ===")

    correct = 0
    total = 0

    for family_id, _primary, texts, _expected_facts in HOLDOUT:
        if family_id != "H4-irrelevant":
            continue

        for variant_index, text in enumerate(texts):
            embedding = _encode([text])[0]

            predicted, similarities = _nearest_centroid(
                embedding,
                centroids,
            )

            expected = "different_work_item"
            is_correct = predicted == expected

            total += 1
            if is_correct:
                correct += 1

            print(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "predicted": predicted,
                    "expected": expected,
                    "correct": is_correct,
                    "similarities": {
                        label: round(score, 4)
                        for label, score in similarities.items()
                    },
                }
            )

    accuracy = correct / total

    print(
        {
            "family": "H4-irrelevant",
            "correct": correct,
            "total": total,
            "accuracy": accuracy,
        }
    )


def test_development_centroid_holdout_is_deterministic() -> None:
    first = _build_development_centroids()
    second = _build_development_centroids()

    assert first.keys() == second.keys()

    for label in first:
        assert np.allclose(
            first[label],
            second[label],
            atol=1e-6,
        )