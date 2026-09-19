from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np

from test_embedding_semantic_separation import MODEL, MODEL_NAME
from test_event_frame_holdout import HOLDOUT


FAMILY_IDS = [family_id for family_id, _primary, _texts, _facts in HOLDOUT]


def _encode(texts: List[str]) -> np.ndarray:
    return MODEL.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )


def _normalize(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        raise ValueError("Cannot normalize zero vector.")
    return vector / norm


def _build_holdout_embeddings() -> Dict[str, np.ndarray]:
    result: Dict[str, np.ndarray] = {}

    for family_id, _primary, texts, _expected_facts in HOLDOUT:
        result[family_id] = _encode(list(texts))

    return result


def _leave_one_out_centroid(
    family_embeddings: np.ndarray,
    excluded_index: int,
) -> np.ndarray:
    remaining = np.delete(family_embeddings, excluded_index, axis=0)
    return _normalize(np.mean(remaining, axis=0))


def _nearest_family(
    embedding: np.ndarray,
    family_centroids: Dict[str, np.ndarray],
) -> Tuple[str, Dict[str, float]]:
    similarities = {
        family_id: float(embedding @ centroid)
        for family_id, centroid in family_centroids.items()
    }

    predicted = max(similarities, key=similarities.get)
    return predicted, similarities


def test_embedding_holdout_leave_one_out_family_centroids() -> None:
    print("\n=== EMBEDDING HOLDOUT LEAVE-ONE-OUT FAMILY CENTROID ===")
    print(f"model={MODEL_NAME}")

    family_embeddings = _build_holdout_embeddings()

    total = 0
    correct = 0

    family_totals: Dict[str, int] = {family_id: 0 for family_id in FAMILY_IDS}
    family_correct: Dict[str, int] = {family_id: 0 for family_id in FAMILY_IDS}

    for family_id, embeddings in family_embeddings.items():
        for variant_index, embedding in enumerate(embeddings):
            family_centroids = {
                other_family_id: _normalize(
                    np.mean(
                        other_embeddings,
                        axis=0,
                    )
                )
                for other_family_id, other_embeddings in family_embeddings.items()
            }

            # Critical diagnostic condition:
            # for the true family, exclude the current example itself.
            family_centroids[family_id] = _leave_one_out_centroid(
                embeddings,
                variant_index,
            )

            predicted, similarities = _nearest_family(
                embedding,
                family_centroids,
            )

            is_correct = predicted == family_id

            total += 1
            family_totals[family_id] += 1

            if is_correct:
                correct += 1
                family_correct[family_id] += 1

            print(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "predicted": predicted,
                    "expected_family": family_id,
                    "correct": is_correct,
                    "similarities": {
                        label: round(score, 4)
                        for label, score in similarities.items()
                    },
                }
            )

    accuracy = correct / total if total else 0.0

    print(
        {
            "model": MODEL_NAME,
            "total_variants": total,
            "leave_one_out_centroid_correct": correct,
            "accuracy": accuracy,
            "fixed_anchor_baseline": "14/20 = 70.0%",
        }
    )

    print("\n=== LEAVE-ONE-OUT CENTROID ACCURACY BY FAMILY ===")

    for family_id in FAMILY_IDS:
        family_accuracy = (
            family_correct[family_id] / family_totals[family_id]
            if family_totals[family_id]
            else 0.0
        )

        print(
            {
                "family": family_id,
                "correct": family_correct[family_id],
                "total": family_totals[family_id],
                "accuracy": family_accuracy,
            }
        )


def test_embedding_holdout_centroid_diagnostic_is_deterministic() -> None:
    first = _build_holdout_embeddings()
    second = _build_holdout_embeddings()

    assert first.keys() == second.keys()

    for family_id in first:
        assert np.allclose(
            first[family_id],
            second[family_id],
            atol=1e-6,
        )