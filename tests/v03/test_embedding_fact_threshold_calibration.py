from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np

from test_clause_local_development_battery import DEVELOPMENT_BATTERY
from test_embedding_semantic_separation import MODEL, MODEL_NAME
from test_event_frame_holdout import HOLDOUT


FACTS = (
    "followup_request",
    "budget_approved",
    "procurement_progressing",
    "commercial_terms_rejected",
    "different_work_item",
    "service_completed",
    "next_step_requested",
)


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


def _development_examples() -> List[Tuple[str, set[str]]]:
    examples: List[Tuple[str, set[str]]] = []

    for _family_id, _primary_state, variants in DEVELOPMENT_BATTERY:
        for text, expected_facts in variants:
            examples.append(
                (
                    text,
                    set(expected_facts),
                )
            )

    return examples


def _build_loo_margin_matrix():
    examples = _development_examples()
    texts = [text for text, _facts in examples]
    expected = [facts for _text, facts in examples]

    embeddings = _encode(texts)

    margins: Dict[str, List[Tuple[float, bool]]] = {
        fact: []
        for fact in FACTS
    }

    for index, embedding in enumerate(embeddings):
        for fact in FACTS:
            positive_indices = [
                i
                for i, facts in enumerate(expected)
                if fact in facts and i != index
            ]

            negative_indices = [
                i
                for i, facts in enumerate(expected)
                if fact not in facts and i != index
            ]

            if not positive_indices or not negative_indices:
                raise ValueError(
                    f"Insufficient leave-one-out data for {fact}"
                )

            positive_centroid = _normalize(
                np.mean(
                    embeddings[positive_indices],
                    axis=0,
                )
            )

            negative_centroid = _normalize(
                np.mean(
                    embeddings[negative_indices],
                    axis=0,
                )
            )

            margin = float(
                embedding @ positive_centroid
                - embedding @ negative_centroid
            )

            margins[fact].append(
                (
                    margin,
                    fact in expected[index],
                )
            )

    return margins


def _candidate_thresholds(
    margins: List[Tuple[float, bool]],
) -> List[float]:
    values = sorted(
        set(
            margin
            for margin, _expected in margins
        )
    )

    candidates = [
        values[0] - 1.0,
        values[-1] + 1.0,
        0.0,
    ]

    for left, right in zip(values, values[1:]):
        candidates.append(
            (left + right) / 2.0
        )

    return sorted(set(candidates))


def _accuracy_at_threshold(
    margins: List[Tuple[float, bool]],
    threshold: float,
) -> float:
    correct = 0

    for margin, expected in margins:
        predicted = margin > threshold

        if predicted == expected:
            correct += 1

    return correct / len(margins)


def _calibrate_thresholds() -> Dict[str, float]:
    margin_matrix = _build_loo_margin_matrix()

    thresholds: Dict[str, float] = {}

    for fact in FACTS:
        margins = margin_matrix[fact]

        candidates = _candidate_thresholds(margins)

        scored = [
            (
                _accuracy_at_threshold(
                    margins,
                    threshold,
                ),
                threshold,
            )
            for threshold in candidates
        ]

        best_accuracy = max(
            accuracy
            for accuracy, _threshold in scored
        )

        best_thresholds = [
            threshold
            for accuracy, threshold in scored
            if accuracy == best_accuracy
        ]

        # Deterministic tie-break:
        # prefer the threshold closest to the original 0.0 rule.
        best_threshold = min(
            best_thresholds,
            key=lambda threshold: (
                abs(threshold),
                threshold,
            ),
        )

        thresholds[fact] = best_threshold

    return thresholds


def _build_full_development_prototypes():
    examples = _development_examples()
    texts = [text for text, _facts in examples]
    expected = [facts for _text, facts in examples]

    embeddings = _encode(texts)

    prototypes = {}

    for fact in FACTS:
        positive_indices = [
            i
            for i, facts in enumerate(expected)
            if fact in facts
        ]

        negative_indices = [
            i
            for i, facts in enumerate(expected)
            if fact not in facts
        ]

        prototypes[fact] = {
            "positive": _normalize(
                np.mean(
                    embeddings[positive_indices],
                    axis=0,
                )
            ),
            "negative": _normalize(
                np.mean(
                    embeddings[negative_indices],
                    axis=0,
                )
            ),
        }

    return prototypes


def _predict_facts(
    embedding: np.ndarray,
    prototypes,
    thresholds: Dict[str, float],
) -> Tuple[set[str], Dict[str, float]]:
    predicted: set[str] = set()
    margins: Dict[str, float] = {}

    for fact in FACTS:
        positive = float(
            embedding @ prototypes[fact]["positive"]
        )

        negative = float(
            embedding @ prototypes[fact]["negative"]
        )

        margin = positive - negative
        margins[fact] = margin

        if margin > thresholds[fact]:
            predicted.add(fact)

    return predicted, margins


def _holdout_examples():
    examples = []

    for family_id, _primary, texts, expected_facts in HOLDOUT:
        for text in texts:
            examples.append(
                (
                    family_id,
                    text,
                    set(expected_facts),
                )
            )

    return examples


def test_development_loo_threshold_calibration() -> None:
    thresholds = _calibrate_thresholds()

    print("\n=== DEVELOPMENT LOO THRESHOLD CALIBRATION ===")
    print(f"model={MODEL_NAME}")

    margin_matrix = _build_loo_margin_matrix()

    for fact in FACTS:
        accuracy = _accuracy_at_threshold(
            margin_matrix[fact],
            thresholds[fact],
        )

        baseline_accuracy = _accuracy_at_threshold(
            margin_matrix[fact],
            0.0,
        )

        print(
            {
                "fact": fact,
                "threshold": round(
                    thresholds[fact],
                    6,
                ),
                "loo_accuracy_at_calibrated_threshold": accuracy,
                "loo_accuracy_at_zero": baseline_accuracy,
            }
        )


def test_calibrated_thresholds_on_unseen_holdout() -> None:
    thresholds = _calibrate_thresholds()
    prototypes = _build_full_development_prototypes()

    print(
        "\n=== DEVELOPMENT-CALIBRATED FACT PROTOTYPES "
        "ON UNSEEN HOLDOUT ==="
    )
    print(f"model={MODEL_NAME}")

    exact_matches = 0
    total_examples = 0

    true_positive = 0
    false_positive = 0
    false_negative = 0

    family_totals: Dict[str, int] = {}
    family_exact: Dict[str, int] = {}

    for family_id, text, expected_facts in _holdout_examples():
        embedding = _encode([text])[0]

        predicted_facts, margins = _predict_facts(
            embedding,
            prototypes,
            thresholds,
        )

        exact = predicted_facts == expected_facts

        total_examples += 1

        family_totals[family_id] = (
            family_totals.get(family_id, 0) + 1
        )

        family_exact[family_id] = (
            family_exact.get(family_id, 0)
            + int(exact)
        )

        if exact:
            exact_matches += 1

        true_positive += len(
            predicted_facts & expected_facts
        )

        false_positive += len(
            predicted_facts - expected_facts
        )

        false_negative += len(
            expected_facts - predicted_facts
        )

        print(
            {
                "family": family_id,
                "expected_facts": sorted(expected_facts),
                "predicted_facts": sorted(predicted_facts),
                "exact_match": exact,
                "margins": {
                    fact: round(
                        margin,
                        4,
                    )
                    for fact, margin in margins.items()
                },
                "thresholds": {
                    fact: round(
                        threshold,
                        4,
                    )
                    for fact, threshold in thresholds.items()
                },
            }
        )

    precision = (
        true_positive
        / (true_positive + false_positive)
        if true_positive + false_positive
        else 0.0
    )

    recall = (
        true_positive
        / (true_positive + false_negative)
        if true_positive + false_negative
        else 0.0
    )

    exact_accuracy = (
        exact_matches / total_examples
    )

    print(
        {
            "model": MODEL_NAME,
            "training_source": "development battery only",
            "threshold_source": "development leave-one-out only",
            "evaluation_source": "unseen holdout only",
            "examples": total_examples,
            "exact_fact_set_matches": exact_matches,
            "exact_fact_set_accuracy": exact_accuracy,
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "micro_precision": precision,
            "micro_recall": recall,
            "zero_threshold_baseline": "17/20 = 85.0%",
        }
    )

    print(
        "\n=== CALIBRATED HOLDOUT EXACT ACCURACY "
        "BY FAMILY ==="
    )

    for family_id in family_totals:
        print(
            {
                "family": family_id,
                "exact": family_exact[family_id],
                "total": family_totals[family_id],
                "accuracy": (
                    family_exact[family_id]
                    / family_totals[family_id]
                ),
            }
        )


def test_calibrated_threshold_negative_control() -> None:
    thresholds = _calibrate_thresholds()
    prototypes = _build_full_development_prototypes()

    print(
        "\n=== CALIBRATED FACT-PROTOTYPE "
        "NEGATIVE CONTROL ==="
    )

    total = 0
    correct = 0

    for family_id, text, expected_facts in _holdout_examples():
        if family_id != "H4-irrelevant":
            continue

        embedding = _encode([text])[0]

        predicted_facts, _margins = _predict_facts(
            embedding,
            prototypes,
            thresholds,
        )

        expected = {"different_work_item"}

        is_correct = predicted_facts == expected

        total += 1

        if is_correct:
            correct += 1

        print(
            {
                "family": family_id,
                "expected": sorted(expected),
                "predicted": sorted(predicted_facts),
                "exact_match": is_correct,
            }
        )

    print(
        {
            "family": "H4-irrelevant",
            "exact_matches": correct,
            "total": total,
            "accuracy": (
                correct / total
                if total
                else 0.0
            ),
        }
    )


def test_calibrated_thresholds_are_deterministic() -> None:
    first = _calibrate_thresholds()
    second = _calibrate_thresholds()

    assert first == second