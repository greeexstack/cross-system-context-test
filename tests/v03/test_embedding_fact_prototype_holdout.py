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


def _build_fact_prototypes() -> Dict[str, Dict[str, np.ndarray]]:
    examples = _development_examples()

    prototypes: Dict[str, Dict[str, np.ndarray]] = {}

    for fact in FACTS:
        positive_texts = [
            text
            for text, expected_facts in examples
            if fact in expected_facts
        ]

        negative_texts = [
            text
            for text, expected_facts in examples
            if fact not in expected_facts
        ]

        assert positive_texts, f"No development positives for {fact}"
        assert negative_texts, f"No development negatives for {fact}"

        positive_centroid = _normalize(
            np.mean(_encode(positive_texts), axis=0)
        )

        negative_centroid = _normalize(
            np.mean(_encode(negative_texts), axis=0)
        )

        prototypes[fact] = {
            "positive": positive_centroid,
            "negative": negative_centroid,
        }

    return prototypes


def _fact_scores(
    embedding: np.ndarray,
    prototypes: Dict[str, Dict[str, np.ndarray]],
) -> Dict[str, Dict[str, float]]:
    scores: Dict[str, Dict[str, float]] = {}

    for fact, prototype in prototypes.items():
        positive_similarity = float(
            embedding @ prototype["positive"]
        )
        negative_similarity = float(
            embedding @ prototype["negative"]
        )

        scores[fact] = {
            "positive_similarity": positive_similarity,
            "negative_similarity": negative_similarity,
            "margin": positive_similarity - negative_similarity,
        }

    return scores


def _predict_facts(
    embedding: np.ndarray,
    prototypes: Dict[str, Dict[str, np.ndarray]],
) -> set[str]:
    scores = _fact_scores(embedding, prototypes)

    return {
        fact
        for fact, values in scores.items()
        if values["margin"] > 0.0
    }


def _holdout_examples() -> List[Tuple[str, str, set[str]]]:
    examples: List[Tuple[str, str, set[str]]] = []

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


def test_development_fact_prototypes_are_complete() -> None:
    prototypes = _build_fact_prototypes()

    print("\n=== DEVELOPMENT FACT PROTOTYPES ===")
    print(f"model={MODEL_NAME}")

    assert set(prototypes) == set(FACTS)

    for fact in FACTS:
        assert prototypes[fact]["positive"].shape == (384,)
        assert prototypes[fact]["negative"].shape == (384,)

        print(
            {
                "fact": fact,
                "positive_examples": sum(
                    fact in expected_facts
                    for _text, expected_facts in _development_examples()
                ),
                "negative_examples": sum(
                    fact not in expected_facts
                    for _text, expected_facts in _development_examples()
                ),
            }
        )


def test_development_fact_prototypes_training_sanity() -> None:
    prototypes = _build_fact_prototypes()

    total_fact_decisions = 0
    correct_fact_decisions = 0

    for text, expected_facts in _development_examples():
        embedding = _encode([text])[0]
        predicted_facts = _predict_facts(
            embedding,
            prototypes,
        )

        for fact in FACTS:
            expected = fact in expected_facts
            predicted = fact in predicted_facts

            total_fact_decisions += 1

            if expected == predicted:
                correct_fact_decisions += 1

    accuracy = correct_fact_decisions / total_fact_decisions

    print("\n=== DEVELOPMENT FACT-PROTOTYPE SANITY ===")
    print(
        {
            "total_binary_fact_decisions": total_fact_decisions,
            "correct": correct_fact_decisions,
            "accuracy": accuracy,
        }
    )

    assert total_fact_decisions == 20 * len(FACTS)


def test_development_fact_prototypes_on_unseen_holdout() -> None:
    prototypes = _build_fact_prototypes()

    print("\n=== DEVELOPMENT-TRAINED FACT PROTOTYPES ON UNSEEN HOLDOUT ===")
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

        predicted_facts = _predict_facts(
            embedding,
            prototypes,
        )

        scores = _fact_scores(
            embedding,
            prototypes,
        )

        exact = predicted_facts == expected_facts

        total_examples += 1

        family_totals[family_id] = family_totals.get(family_id, 0) + 1
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
                    fact: round(values["margin"], 4)
                    for fact, values in scores.items()
                },
                "text": text,
            }
        )

    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else 0.0
    )

    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative
        else 0.0
    )

    exact_accuracy = exact_matches / total_examples

    print(
        {
            "model": MODEL_NAME,
            "training_source": "development battery only",
            "evaluation_source": "unseen holdout only",
            "examples": total_examples,
            "exact_fact_set_matches": exact_matches,
            "exact_fact_set_accuracy": exact_accuracy,
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "micro_precision": precision,
            "micro_recall": recall,
        }
    )

    print("\n=== HOLDOUT EXACT FACT-SET ACCURACY BY FAMILY ===")

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


def test_development_fact_prototypes_negative_control() -> None:
    prototypes = _build_fact_prototypes()

    print("\n=== DEVELOPMENT-TRAINED FACT PROTOTYPE NEGATIVE CONTROL ===")

    total = 0
    correct = 0

    for family_id, text, expected_facts in _holdout_examples():
        if family_id != "H4-irrelevant":
            continue

        embedding = _encode([text])[0]
        predicted_facts = _predict_facts(
            embedding,
            prototypes,
        )

        expected = {"different_work_item"}

        is_correct = predicted_facts == expected

        total += 1
        if is_correct:
            correct += 1

        print(
            {
                "family": family_id,
                "expected_facts": sorted(expected_facts),
                "predicted_facts": sorted(predicted_facts),
                "expected_negative_control": sorted(expected),
                "exact_match": is_correct,
                "text": text,
            }
        )

    print(
        {
            "family": "H4-irrelevant",
            "exact_matches": correct,
            "total": total,
            "accuracy": correct / total if total else 0.0,
        }
    )


def test_development_fact_prototype_holdout_is_deterministic() -> None:
    first = _build_fact_prototypes()
    second = _build_fact_prototypes()

    assert first.keys() == second.keys()

    for fact in FACTS:
        assert np.allclose(
            first[fact]["positive"],
            second[fact]["positive"],
            atol=1e-6,
        )
        assert np.allclose(
            first[fact]["negative"],
            second[fact]["negative"],
            atol=1e-6,
        )