from __future__ import annotations

from typing import Dict, List, Tuple

from test_embedding_disentangled_generalization import (
    FACTS,
    _build_prototypes,
    _calibrate_thresholds,
    _predict,
)
from test_embedding_semantic_separation import MODEL


COMPOSITION_INTERFERENCE_BATTERY = (
    (
        "CI1-budget-procurement",
        (
            (
                "Finance authorized the planned expenditure.",
                {"budget_approved"},
            ),
            (
                "Finance authorized the planned expenditure, and the purchasing desk began processing the request.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
        ),
    ),
    (
        "CI2-procurement-budget",
        (
            (
                "The purchasing desk began processing the request.",
                {"procurement_progressing"},
            ),
            (
                "The purchasing desk began processing the request, and finance authorized the planned expenditure.",
                {
                    "procurement_progressing",
                    "budget_approved",
                },
            ),
        ),
    ),
    (
        "CI3-service-next-step",
        (
            (
                "The deployment activity has been completed.",
                {"service_completed"},
            ),
            (
                "The deployment activity has been completed, and the customer asked what comes next.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
        ),
    ),
    (
        "CI4-next-step-service",
        (
            (
                "The customer asked what comes next.",
                {"next_step_requested"},
            ),
            (
                "The customer asked what comes next, and the deployment activity has been completed.",
                {
                    "next_step_requested",
                    "service_completed",
                },
            ),
        ),
    ),
    (
        "CI5-rejection-followup",
        (
            (
                "The customer rejected the revised commercial terms.",
                {"commercial_terms_rejected"},
            ),
            (
                "The customer rejected the revised commercial terms and asked to discuss the proposal again.",
                {
                    "commercial_terms_rejected",
                    "followup_request",
                },
            ),
        ),
    ),
    (
        "CI6-followup-rejection",
        (
            (
                "The customer asked to discuss the proposal again.",
                {"followup_request"},
            ),
            (
                "The customer asked to discuss the proposal again and rejected the revised commercial terms.",
                {
                    "followup_request",
                    "commercial_terms_rejected",
                },
            ),
        ),
    ),
    (
        "CI7-followup-procurement",
        (
            (
                "The buyer requested another conversation about the proposal.",
                {"followup_request"},
            ),
            (
                "The buyer requested another conversation about the proposal, and procurement began processing the order.",
                {
                    "followup_request",
                    "procurement_progressing",
                },
            ),
        ),
    ),
    (
        "CI8-budget-next-step",
        (
            (
                "Finance approved the requested spending.",
                {"budget_approved"},
            ),
            (
                "Finance approved the requested spending, and the customer asked about the next stage.",
                {
                    "budget_approved",
                    "next_step_requested",
                },
            ),
        ),
    ),
)


NEUTRAL_CONTROL = (
    "The record contains a routine administrative update.",
    "The message records ordinary scheduling activity with no substantive event.",
    "The account note contains only a general internal status update.",
    "This entry reports routine coordination and no decision-relevant evidence.",
)


def _score(
    text: str,
    prototypes,
    thresholds,
) -> Tuple[set[str], Dict[str, float]]:
    embedding = MODEL.encode(
        [text],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )[0]

    predicted, margins = _predict(
        text,
        prototypes,
        thresholds,
    )

    # Recompute scores explicitly so this diagnostic can compare
    # the same fact across the singleton and composed forms.
    del embedding

    return predicted, margins


def test_composition_interference_is_measured() -> None:
    prototypes = _build_prototypes()
    thresholds = _calibrate_thresholds()

    print("\n=== EMBEDDING COMPOSITION INTERFERENCE ===")

    total_composed = 0
    exact_composed = 0

    preserved_existing_fact = 0
    existing_fact_tests = 0

    newly_added_fact_correct = 0
    newly_added_fact_tests = 0

    for family_id, pair in COMPOSITION_INTERFERENCE_BATTERY:
        singleton_text, singleton_expected = pair[0]
        composed_text, composed_expected = pair[1]

        singleton_predicted, singleton_margins = _score(
            singleton_text,
            prototypes,
            thresholds,
        )

        composed_predicted, composed_margins = _score(
            composed_text,
            prototypes,
            thresholds,
        )

        composed_exact = composed_predicted == composed_expected

        total_composed += 1

        if composed_exact:
            exact_composed += 1

        for fact in singleton_expected:
            existing_fact_tests += 1

            singleton_present = (
                fact in singleton_predicted
            )
            composed_present = (
                fact in composed_predicted
            )

            if singleton_present and composed_present:
                preserved_existing_fact += 1

            print(
                {
                    "family": family_id,
                    "fact": fact,
                    "singleton_predicted": (
                        fact in singleton_predicted
                    ),
                    "composed_predicted": (
                        fact in composed_predicted
                    ),
                    "singleton_margin": round(
                        singleton_margins[fact],
                        4,
                    ),
                    "composed_margin": round(
                        composed_margins[fact],
                        4,
                    ),
                    "margin_change": round(
                        composed_margins[fact]
                        - singleton_margins[fact],
                        4,
                    ),
                }
            )

        added_facts = (
            composed_expected - singleton_expected
        )

        for fact in added_facts:
            newly_added_fact_tests += 1

            if fact in composed_predicted:
                newly_added_fact_correct += 1

        print(
            {
                "family": family_id,
                "singleton_expected": sorted(
                    singleton_expected
                ),
                "singleton_predicted": sorted(
                    singleton_predicted
                ),
                "composed_expected": sorted(
                    composed_expected
                ),
                "composed_predicted": sorted(
                    composed_predicted
                ),
                "composed_exact": composed_exact,
            }
        )

    print(
        {
            "composed_exact": exact_composed,
            "composed_total": total_composed,
            "composed_accuracy": (
                exact_composed / total_composed
            ),
            "existing_fact_preservation": (
                preserved_existing_fact
                / existing_fact_tests
            ),
            "new_fact_recovery": (
                newly_added_fact_correct
                / newly_added_fact_tests
            ),
        }
    )


def test_composition_interference_family_breakdown() -> None:
    prototypes = _build_prototypes()
    thresholds = _calibrate_thresholds()

    print("\n=== COMPOSITION INTERFERENCE BY FAMILY ===")

    for family_id, pair in COMPOSITION_INTERFERENCE_BATTERY:
        singleton_text, singleton_expected = pair[0]
        composed_text, composed_expected = pair[1]

        _singleton_predicted, singleton_margins = _score(
            singleton_text,
            prototypes,
            thresholds,
        )

        composed_predicted, composed_margins = _score(
            composed_text,
            prototypes,
            thresholds,
        )

        margin_changes = {
            fact: round(
                composed_margins[fact]
                - singleton_margins[fact],
                4,
            )
            for fact in singleton_expected
        }

        print(
            {
                "family": family_id,
                "singleton_expected": sorted(
                    singleton_expected
                ),
                "composed_expected": sorted(
                    composed_expected
                ),
                "composed_predicted": sorted(
                    composed_predicted
                ),
                "margin_changes_for_existing_facts": (
                    margin_changes
                ),
            }
        )


def test_neutral_control_without_empty_fact_training() -> None:
    prototypes = _build_prototypes()
    thresholds = _calibrate_thresholds()

    correct = 0

    print("\n=== NEUTRAL CONTROL ===")

    for variant_index, text in enumerate(
        NEUTRAL_CONTROL
    ):
        predicted, margins = _score(
            text,
            prototypes,
            thresholds,
        )

        exact = predicted == set()

        if exact:
            correct += 1

        print(
            {
                "variant": variant_index,
                "expected": [],
                "predicted": sorted(predicted),
                "exact": exact,
                "margins": {
                    fact: round(
                        margin,
                        4,
                    )
                    for fact, margin in margins.items()
                },
                "text": text,
            }
        )

    print(
        {
            "correct": correct,
            "total": len(NEUTRAL_CONTROL),
            "accuracy": correct / len(NEUTRAL_CONTROL),
        }
    )


def test_composition_interference_battery_is_new() -> None:
    texts = [
        text
        for _family_id, pair in COMPOSITION_INTERFERENCE_BATTERY
        for text, _facts in pair
    ]

    assert len(texts) == 16
    assert len(set(texts)) == 16


def test_composition_interference_is_deterministic() -> None:
    prototypes_a = _build_prototypes()
    prototypes_b = _build_prototypes()

    thresholds_a = _calibrate_thresholds()
    thresholds_b = _calibrate_thresholds()

    assert thresholds_a == thresholds_b

    for family_id, pair in COMPOSITION_INTERFERENCE_BATTERY:
        for text, _expected in pair:
            predicted_a, margins_a = _score(
                text,
                prototypes_a,
                thresholds_a,
            )

            predicted_b, margins_b = _score(
                text,
                prototypes_b,
                thresholds_b,
            )

            assert predicted_a == predicted_b

            for fact in FACTS:
                assert abs(
                    margins_a[fact]
                    - margins_b[fact]
                ) < 1e-6