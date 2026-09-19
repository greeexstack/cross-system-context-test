from __future__ import annotations

from test_embedding_fact_disentanglement_battery import (
    DISENTANGLEMENT_BATTERY,
)
from test_embedding_fact_threshold_calibration import (
    _build_full_development_prototypes,
    _calibrate_thresholds,
    _predict_facts,
)
from test_embedding_semantic_separation import MODEL


def _predict(
    text: str,
    prototypes,
    thresholds,
) -> set[str]:
    embedding = MODEL.encode(
        [text],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )[0]

    predicted, _margins = _predict_facts(
        embedding,
        prototypes,
        thresholds,
    )

    return predicted


def test_frozen_embedding_fact_disentanglement() -> None:
    prototypes = _build_full_development_prototypes()
    thresholds = _calibrate_thresholds()

    total = 0
    exact = 0

    false_positive_cases = []
    false_negative_cases = []

    print("\n=== FROZEN EMBEDDING FACT DISENTANGLEMENT ===")

    for family_id, variants in DISENTANGLEMENT_BATTERY:
        family_total = 0
        family_exact = 0

        for variant_index, (text, expected_facts) in enumerate(
            variants,
            start=0,
        ):
            predicted_facts = _predict(
                text,
                prototypes,
                thresholds,
            )

            is_exact = predicted_facts == expected_facts

            total += 1
            family_total += 1

            if is_exact:
                exact += 1
                family_exact += 1

            false_positives = (
                predicted_facts - expected_facts
            )
            false_negatives = (
                expected_facts - predicted_facts
            )

            if false_positives:
                false_positive_cases.append(
                    {
                        "family": family_id,
                        "variant": variant_index,
                        "false_positives": sorted(
                            false_positives
                        ),
                        "expected": sorted(
                            expected_facts
                        ),
                        "predicted": sorted(
                            predicted_facts
                        ),
                        "text": text,
                    }
                )

            if false_negatives:
                false_negative_cases.append(
                    {
                        "family": family_id,
                        "variant": variant_index,
                        "false_negatives": sorted(
                            false_negatives
                        ),
                        "expected": sorted(
                            expected_facts
                        ),
                        "predicted": sorted(
                            predicted_facts
                        ),
                        "text": text,
                    }
                )

            print(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "expected": sorted(
                        expected_facts
                    ),
                    "predicted": sorted(
                        predicted_facts
                    ),
                    "exact": is_exact,
                }
            )

        print(
            {
                "family": family_id,
                "exact": family_exact,
                "total": family_total,
                "accuracy": (
                    family_exact / family_total
                ),
            }
        )

    print("\n=== DISENTANGLEMENT SUMMARY ===")
    print(
        {
            "total": total,
            "exact": exact,
            "exact_accuracy": exact / total,
            "false_positive_cases": len(
                false_positive_cases
            ),
            "false_negative_cases": len(
                false_negative_cases
            ),
        }
    )

    print("\n=== FALSE POSITIVE CASES ===")
    for case in false_positive_cases:
        print(case)

    print("\n=== FALSE NEGATIVE CASES ===")
    for case in false_negative_cases:
        print(case)

    assert total == 24


def test_budget_and_procurement_are_disentangled() -> None:
    prototypes = _build_full_development_prototypes()
    thresholds = _calibrate_thresholds()

    budget_only = next(
        variants
        for family_id, variants in DISENTANGLEMENT_BATTERY
        if family_id == "F1-budget-only"
    )

    procurement_only = next(
        variants
        for family_id, variants in DISENTANGLEMENT_BATTERY
        if family_id == "F2-procurement-only"
    )

    budget_only_correct = 0
    procurement_only_correct = 0

    for text, expected_facts in budget_only:
        predicted = _predict(
            text,
            prototypes,
            thresholds,
        )

        if predicted == expected_facts:
            budget_only_correct += 1

    for text, expected_facts in procurement_only:
        predicted = _predict(
            text,
            prototypes,
            thresholds,
        )

        if predicted == expected_facts:
            procurement_only_correct += 1

    print(
        "\n=== BUDGET / PROCUREMENT DISENTANGLEMENT ==="
    )
    print(
        {
            "budget_only_exact": budget_only_correct,
            "budget_only_total": len(budget_only),
            "procurement_only_exact": procurement_only_correct,
            "procurement_only_total": len(
                procurement_only
            ),
        }
    )


def test_service_and_next_step_are_disentangled() -> None:
    prototypes = _build_full_development_prototypes()
    thresholds = _calibrate_thresholds()

    service_only = next(
        variants
        for family_id, variants in DISENTANGLEMENT_BATTERY
        if family_id == "F3-service-completion-only"
    )

    next_step_only = next(
        variants
        for family_id, variants in DISENTANGLEMENT_BATTERY
        if family_id == "F4-next-step-only"
    )

    service_only_correct = 0
    next_step_only_correct = 0

    for text, expected_facts in service_only:
        predicted = _predict(
            text,
            prototypes,
            thresholds,
        )

        if predicted == expected_facts:
            service_only_correct += 1

    for text, expected_facts in next_step_only:
        predicted = _predict(
            text,
            prototypes,
            thresholds,
        )

        if predicted == expected_facts:
            next_step_only_correct += 1

    print(
        "\n=== SERVICE / NEXT-STEP DISENTANGLEMENT ==="
    )
    print(
        {
            "service_only_exact": service_only_correct,
            "service_only_total": len(service_only),
            "next_step_only_exact": next_step_only_correct,
            "next_step_only_total": len(
                next_step_only
            ),
        }
    )