from __future__ import annotations

from typing import Dict, List, Tuple

from sentence_transformers import SentenceTransformer

from test_embedding_semantic_separation import ANCHORS, CENTROIDS, MODEL, MODEL_NAME
from test_event_frame_holdout import HOLDOUT


# Independent evaluation mapping.
#
# The candidate sees only the holdout text. These labels are used only by the
# test to determine whether the nearest semantic anchor matches the semantic
# family represented by the frozen holdout.
EXPECTED_ANCHOR_BY_FAMILY = {
    "H1-followup": "followup",
    "H2-supporting": "approval",
    "H3-contradictory": "rejection",
    "H4-irrelevant": "different_work_item",
    "H5-service-next-step": "next_step",
}


def _encode(texts: List[str]):
    return MODEL.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )


def _nearest_anchor(text: str) -> Tuple[str, Dict[str, float]]:
    embedding = _encode([text])[0]

    similarities = {
        label: float(embedding @ centroid)
        for label, centroid in CENTROIDS.items()
    }

    predicted = max(similarities, key=similarities.get)
    return predicted, similarities


def test_embedding_holdout_nearest_anchor() -> None:
    print("\n=== EMBEDDING UNSEEN HOLDOUT NEAREST-ANCHOR ===")
    print(f"model={MODEL_NAME}")
    print(f"anchor_labels={list(ANCHORS)}")

    total = 0
    correct = 0
    family_totals: Dict[str, int] = {}
    family_correct: Dict[str, int] = {}

    for family_id, _primary, texts, _expected_facts in HOLDOUT:
        expected_anchor = EXPECTED_ANCHOR_BY_FAMILY[family_id]

        family_totals[family_id] = 0
        family_correct[family_id] = 0

        for variant_index, text in enumerate(texts):
            predicted, similarities = _nearest_anchor(text)

            is_correct = predicted == expected_anchor

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
                    "expected_anchor": expected_anchor,
                    "correct": is_correct,
                    "similarities": {
                        label: round(score, 4)
                        for label, score in similarities.items()
                    },
                    "text": text,
                }
            )

    accuracy = correct / total if total else 0.0

    print(
        {
            "model": MODEL_NAME,
            "total_variants": total,
            "nearest_anchor_correct": correct,
            "accuracy": accuracy,
        }
    )

    print("\n=== HOLDOUT ACCURACY BY FAMILY ===")

    for family_id in EXPECTED_ANCHOR_BY_FAMILY:
        family_accuracy = (
            family_correct[family_id] / family_totals[family_id]
            if family_totals[family_id]
            else 0.0
        )

        print(
            {
                "family": family_id,
                "expected_anchor": EXPECTED_ANCHOR_BY_FAMILY[family_id],
                "correct": family_correct[family_id],
                "total": family_totals[family_id],
                "accuracy": family_accuracy,
            }
        )


def test_embedding_holdout_negative_control() -> None:
    print("\n=== EMBEDDING HOLDOUT NEGATIVE CONTROL ===")

    family_id = "H4-irrelevant"
    expected_anchor = EXPECTED_ANCHOR_BY_FAMILY[family_id]

    total = 0
    correct = 0

    for holdout_family_id, _primary, texts, _expected_facts in HOLDOUT:
        if holdout_family_id != family_id:
            continue

        for variant_index, text in enumerate(texts):
            predicted, similarities = _nearest_anchor(text)
            is_correct = predicted == expected_anchor

            total += 1
            if is_correct:
                correct += 1

            print(
                {
                    "family": holdout_family_id,
                    "variant": variant_index,
                    "predicted": predicted,
                    "expected_anchor": expected_anchor,
                    "correct": is_correct,
                    "similarities": {
                        label: round(score, 4)
                        for label, score in similarities.items()
                    },
                    "text": text,
                }
            )

    accuracy = correct / total if total else 0.0

    print(
        {
            "family": family_id,
            "correct": correct,
            "total": total,
            "accuracy": accuracy,
        }
    )


def test_embedding_holdout_is_deterministic() -> None:
    print("\n=== EMBEDDING HOLDOUT DETERMINISM ===")

    samples = [
        (family_id, text)
        for family_id, _primary, texts, _expected_facts in HOLDOUT
        for text in texts
    ]

    first_run = [
        (_nearest_anchor(text)[0], _nearest_anchor(text)[1])
        for _family_id, text in samples
    ]

    second_run = [
        (_nearest_anchor(text)[0], _nearest_anchor(text)[1])
        for _family_id, text in samples
    ]

    assert len(first_run) == len(second_run)

    for first, second in zip(first_run, second_run):
        first_label, first_scores = first
        second_label, second_scores = second

        assert first_label == second_label

        for label in first_scores:
            assert abs(first_scores[label] - second_scores[label]) < 1e-6