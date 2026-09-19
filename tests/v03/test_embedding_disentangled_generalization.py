from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Tuple

import numpy as np

from test_embedding_disentangled_development_battery import (
    DISENTANGLED_DEVELOPMENT_BATTERY,
)
from test_embedding_semantic_separation import MODEL


FACTS = (
    "followup_request",
    "budget_approved",
    "procurement_progressing",
    "commercial_terms_rejected",
    "different_work_item",
    "service_completed",
    "next_step_requested",
)


# This is a NEW evaluation battery.
#
# It is deliberately different from:
# - the original development battery,
# - the original unseen holdout,
# - the construction battery,
# - the hybrid battery.
#
# It contains singleton facts plus genuinely compositional cases.
GENERALIZATION_BATTERY = (
    (
        "G1-followup",
        (
            (
                "The account team wants to reopen the proposal discussion after the internal review.",
                {"followup_request"},
            ),
            (
                "The buyer requested another conversation once the quotation has been considered.",
                {"followup_request"},
            ),
            (
                "The customer asked to pick up the commercial discussion again later this week.",
                {"followup_request"},
            ),
            (
                "The purchaser would like the proposal conversation continued after review.",
                {"followup_request"},
            ),
        ),
    ),
    (
        "G2-budget",
        (
            (
                "The finance director authorized the planned purchase.",
                {"budget_approved"},
            ),
            (
                "Approval was issued for the proposed level of spending.",
                {"budget_approved"},
            ),
            (
                "The requested funding received sign-off from finance.",
                {"budget_approved"},
            ),
            (
                "The organization cleared the expenditure request.",
                {"budget_approved"},
            ),
        ),
    ),
    (
        "G3-procurement",
        (
            (
                "The purchasing office has begun working on the order.",
                {"procurement_progressing"},
            ),
            (
                "The sourcing team has moved the request into processing.",
                {"procurement_progressing"},
            ),
            (
                "The buying workflow is actively handling the requisition.",
                {"procurement_progressing"},
            ),
            (
                "Procurement has started advancing the purchase request.",
                {"procurement_progressing"},
            ),
        ),
    ),
    (
        "G4-rejection",
        (
            (
                "The revised commercial package was rejected by the customer.",
                {"commercial_terms_rejected"},
            ),
            (
                "The buyer declined the updated business terms.",
                {"commercial_terms_rejected"},
            ),
            (
                "The client would not proceed under the amended commercial arrangement.",
                {"commercial_terms_rejected"},
            ),
            (
                "The customer ruled against the revised terms and requested changes.",
                {"commercial_terms_rejected"},
            ),
        ),
    ),
    (
        "G5-different-work-item",
        (
            (
                "This note concerns a separate customer program rather than the quotation under review.",
                {"different_work_item"},
            ),
            (
                "The update is about another deployment and does not concern the current opportunity.",
                {"different_work_item"},
            ),
            (
                "The team is discussing a different implementation, not this proposal.",
                {"different_work_item"},
            ),
            (
                "The customer's latest discussion relates to another site and not the present deal.",
                {"different_work_item"},
            ),
        ),
    ),
    (
        "G6-service-completed",
        (
            (
                "The implementation activity has reached completion.",
                {"service_completed"},
            ),
            (
                "The deployment work is fully finished.",
                {"service_completed"},
            ),
            (
                "The migration operation has come to an end.",
                {"service_completed"},
            ),
            (
                "The service rollout has been completed successfully.",
                {"service_completed"},
            ),
        ),
    ),
    (
        "G7-next-step",
        (
            (
                "The customer asked for clarification about the following stage.",
                {"next_step_requested"},
            ),
            (
                "The client wants to understand the next part of the process.",
                {"next_step_requested"},
            ),
            (
                "The buyer requested details about the subsequent action.",
                {"next_step_requested"},
            ),
            (
                "The customer asked what should happen after this point.",
                {"next_step_requested"},
            ),
        ),
    ),
    (
        "G8-budget-and-procurement",
        (
            (
                "The finance office approved the request while purchasing began processing it.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
            (
                "Funding was cleared and the buying operation moved into execution.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
            (
                "The expenditure received authorization as procurement started the order workflow.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
            (
                "Financial approval was granted and sourcing began handling the purchase.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
        ),
    ),
    (
        "G9-service-and-next-step",
        (
            (
                "The rollout has ended and the customer is asking about the next phase.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
            (
                "The implementation is complete, and the client wants to know what follows.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
            (
                "The deployment has finished and guidance is requested for the subsequent stage.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
            (
                "The service activity concluded while the customer asked about the ensuing transition.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
        ),
    ),
    (
        "G10-rejection-and-followup",
        (
            (
                "The customer rejected the revised arrangement but requested another discussion.",
                {
                    "commercial_terms_rejected",
                    "followup_request",
                },
            ),
            (
                "The buyer declined the updated terms and asked to revisit the proposal.",
                {
                    "commercial_terms_rejected",
                    "followup_request",
                },
            ),
            (
                "The amended deal was refused, with the client requesting a further conversation.",
                {
                    "commercial_terms_rejected",
                    "followup_request",
                },
            ),
            (
                "The purchaser would not accept the new conditions and wants the discussion resumed.",
                {
                    "commercial_terms_rejected",
                    "followup_request",
                },
            ),
        ),
    ),
    (
        "G11-neutral",
        (
            (
                "The account record contains only a general administrative note.",
                set(),
            ),
            (
                "The message records a routine internal update with no substantive event.",
                set(),
            ),
            (
                "This entry contains a scheduling note unrelated to the evidence categories.",
                set(),
            ),
            (
                "The record reports ordinary account maintenance and no decision-relevant event.",
                set(),
            ),
        ),
    ),
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

    for _family_id, variants in DISENTANGLED_DEVELOPMENT_BATTERY:
        for text, expected_facts in variants:
            examples.append(
                (
                    text,
                    set(expected_facts),
                )
            )

    return examples


def _build_prototypes():
    examples = _development_examples()

    texts = [text for text, _facts in examples]
    expected = [facts for _text, facts in examples]

    embeddings = _encode(texts)

    prototypes: Dict[str, Dict[str, np.ndarray]] = {}

    for fact in FACTS:
        positive = [
            embeddings[index]
            for index, facts in enumerate(expected)
            if fact in facts
        ]

        negative = [
            embeddings[index]
            for index, facts in enumerate(expected)
            if fact not in facts
        ]

        assert positive
        assert negative

        prototypes[fact] = {
            "positive": _normalize(
                np.mean(positive, axis=0)
            ),
            "negative": _normalize(
                np.mean(negative, axis=0)
            ),
        }

    return prototypes


def _loo_margins():
    examples = _development_examples()

    texts = [text for text, _facts in examples]
    expected = [facts for _text, facts in examples]

    embeddings = _encode(texts)

    result: Dict[str, List[Tuple[float, bool]]] = {
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

            result[fact].append(
                (
                    margin,
                    fact in expected[index],
                )
            )

    return result


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
    margins = _loo_margins()

    thresholds: Dict[str, float] = {}

    for fact in FACTS:
        candidates = _candidate_thresholds(
            margins[fact]
        )

        scored = [
            (
                _accuracy_at_threshold(
                    margins[fact],
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

        best = [
            threshold
            for accuracy, threshold in scored
            if accuracy == best_accuracy
        ]

        thresholds[fact] = min(
            best,
            key=lambda threshold: (
                abs(threshold),
                threshold,
            ),
        )

    return thresholds


def _predict(
    text: str,
    prototypes,
    thresholds,
) -> Tuple[set[str], Dict[str, float]]:
    embedding = _encode([text])[0]

    margins: Dict[str, float] = {}
    predicted: set[str] = set()

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


def test_generalization_battery_is_new_and_controlled() -> None:
    development_texts = {
        text
        for _family_id, variants in DISENTANGLED_DEVELOPMENT_BATTERY
        for text, _facts in variants
    }

    evaluation_texts = {
        text
        for _family_id, variants in GENERALIZATION_BATTERY
        for text, _facts in variants
    }

    assert len(GENERALIZATION_BATTERY) == 11
    assert len(evaluation_texts) == 44

    # No evaluation text may have appeared in the disentangled training set.
    assert development_texts.isdisjoint(evaluation_texts)

    # Every evaluation family has exactly four variants.
    for family_id, variants in GENERALIZATION_BATTERY:
        assert family_id.startswith("G")
        assert len(variants) == 4


def test_disentangled_training_leave_one_out_sanity() -> None:
    print("\n=== DISENTANGLED TRAINING LOO SANITY ===")

    margins = _loo_margins()

    total = 0
    correct = 0

    for fact in FACTS:
        accuracy = _accuracy_at_threshold(
            margins[fact],
            0.0,
        )

        print(
            {
                "fact": fact,
                "loo_accuracy_at_zero": accuracy,
            }
        )

        for margin, expected in margins[fact]:
            total += 1

            if (margin > 0.0) == expected:
                correct += 1

    print(
        {
            "total_binary_decisions": total,
            "correct": correct,
            "accuracy": correct / total,
        }
    )

    assert total == 28 * len(FACTS)


def test_disentangled_prototypes_on_unseen_generalization() -> None:
    prototypes = _build_prototypes()
    thresholds = _calibrate_thresholds()

    print(
        "\n=== DISENTANGLED DEVELOPMENT "
        "PROTOTYPES ON NEW GENERALIZATION BATTERY ==="
    )

    total = 0
    exact = 0

    true_positive = 0
    false_positive = 0
    false_negative = 0

    family_total: Dict[str, int] = {}
    family_exact: Dict[str, int] = {}

    for family_id, variants in GENERALIZATION_BATTERY:
        for variant_index, (text, expected) in enumerate(
            variants,
            start=0,
        ):
            predicted, margins = _predict(
                text,
                prototypes,
                thresholds,
            )

            is_exact = predicted == expected

            total += 1
            family_total[family_id] = (
                family_total.get(family_id, 0) + 1
            )
            family_exact[family_id] = (
                family_exact.get(family_id, 0)
                + int(is_exact)
            )

            if is_exact:
                exact += 1

            true_positive += len(
                predicted & expected
            )

            false_positive += len(
                predicted - expected
            )

            false_negative += len(
                expected - predicted
            )

            print(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "expected": sorted(expected),
                    "predicted": sorted(predicted),
                    "exact": is_exact,
                    "margins": {
                        fact: round(
                            margin,
                            4,
                        )
                        for fact, margin in margins.items()
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

    print("\n=== GENERALIZATION SUMMARY ===")
    print(
        {
            "examples": total,
            "exact_fact_sets": exact,
            "exact_accuracy": exact / total,
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "micro_precision": precision,
            "micro_recall": recall,
        }
    )

    print("\n=== GENERALIZATION BY FAMILY ===")

    for family_id in family_total:
        print(
            {
                "family": family_id,
                "exact": family_exact[family_id],
                "total": family_total[family_id],
                "accuracy": (
                    family_exact[family_id]
                    / family_total[family_id]
                ),
            }
        )


def test_singleton_fact_disentanglement() -> None:
    prototypes = _build_prototypes()
    thresholds = _calibrate_thresholds()

    print("\n=== SINGLETON FACT DISENTANGLEMENT ===")

    singleton_families = {
        "G1-followup",
        "G2-budget",
        "G3-procurement",
        "G4-rejection",
        "G5-different-work-item",
        "G6-service-completed",
        "G7-next-step",
    }

    total = 0
    exact = 0

    for family_id, variants in GENERALIZATION_BATTERY:
        if family_id not in singleton_families:
            continue

        family_exact = 0

        for text, expected in variants:
            predicted, _margins = _predict(
                text,
                prototypes,
                thresholds,
            )

            total += 1

            if predicted == expected:
                exact += 1
                family_exact += 1

        print(
            {
                "family": family_id,
                "exact": family_exact,
                "total": len(variants),
                "accuracy": family_exact / len(variants),
            }
        )

    print(
        {
            "singleton_exact": exact,
            "singleton_total": total,
            "singleton_accuracy": exact / total,
        }
    )


def test_compositional_fact_recovery() -> None:
    prototypes = _build_prototypes()
    thresholds = _calibrate_thresholds()

    print("\n=== COMPOSITIONAL FACT RECOVERY ===")

    composition_families = {
        "G8-budget-and-procurement",
        "G9-service-and-next-step",
        "G10-rejection-and-followup",
    }

    total = 0
    exact = 0

    for family_id, variants in GENERALIZATION_BATTERY:
        if family_id not in composition_families:
            continue

        family_exact = 0

        for text, expected in variants:
            predicted, _margins = _predict(
                text,
                prototypes,
                thresholds,
            )

            total += 1

            if predicted == expected:
                exact += 1
                family_exact += 1

        print(
            {
                "family": family_id,
                "exact": family_exact,
                "total": len(variants),
                "accuracy": family_exact / len(variants),
            }
        )

    print(
        {
            "composition_exact": exact,
            "composition_total": total,
            "composition_accuracy": exact / total,
        }
    )


def test_neutral_negative_control() -> None:
    prototypes = _build_prototypes()
    thresholds = _calibrate_thresholds()

    neutral = next(
        variants
        for family_id, variants in GENERALIZATION_BATTERY
        if family_id == "G11-neutral"
    )

    correct = 0

    print("\n=== NEUTRAL NEGATIVE CONTROL ===")

    for variant_index, (text, expected) in enumerate(neutral):
        predicted, _margins = _predict(
            text,
            prototypes,
            thresholds,
        )

        is_correct = predicted == expected

        if is_correct:
            correct += 1

        print(
            {
                "variant": variant_index,
                "expected": sorted(expected),
                "predicted": sorted(predicted),
                "exact": is_correct,
            }
        )

    print(
        {
            "correct": correct,
            "total": len(neutral),
            "accuracy": correct / len(neutral),
        }
    )


def test_generalization_results_are_deterministic() -> None:
    prototypes_a = _build_prototypes()
    prototypes_b = _build_prototypes()

    thresholds_a = _calibrate_thresholds()
    thresholds_b = _calibrate_thresholds()

    assert thresholds_a == thresholds_b

    for fact in FACTS:
        assert np.allclose(
            prototypes_a[fact]["positive"],
            prototypes_b[fact]["positive"],
            atol=1e-6,
        )

        assert np.allclose(
            prototypes_a[fact]["negative"],
            prototypes_b[fact]["negative"],
            atol=1e-6,
        )