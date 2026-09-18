from __future__ import annotations

from test_event_frame_holdout import HOLDOUT
from test_holdout_representation_comparison import (
    _candidate_core_facts,
    _old_core_facts,
)


def _metrics(
    observed: set[str],
    expected: set[str],
) -> dict[str, object]:
    correct = observed.intersection(expected)

    precision = (
        len(correct) / len(observed)
        if observed
        else 0.0
    )

    recall = (
        len(correct) / len(expected)
        if expected
        else 1.0
    )

    exact = observed == expected

    return {
        "observed": sorted(observed),
        "expected": sorted(expected),
        "correct": sorted(correct),
        "precision": precision,
        "recall": recall,
        "exact": exact,
    }


def test_holdout_factual_accuracy_old_vs_candidate() -> None:
    old_total_precision = 0.0
    candidate_total_precision = 0.0

    old_total_recall = 0.0
    candidate_total_recall = 0.0

    old_exact = 0
    candidate_exact = 0

    variants = 0

    print(
        "\n=== HOLDOUT FACTUAL ACCURACY ==="
    )

    for family_id, _primary, texts, expected in HOLDOUT:
        for variant_index, text in enumerate(
            texts,
            start=0,
        ):
            variants += 1

            old_observed = _old_core_facts(text)
            candidate_observed = _candidate_core_facts(
                text
            )

            old = _metrics(
                old_observed,
                expected,
            )
            candidate = _metrics(
                candidate_observed,
                expected,
            )

            old_total_precision += old["precision"]
            candidate_total_precision += (
                candidate["precision"]
            )

            old_total_recall += old["recall"]
            candidate_total_recall += (
                candidate["recall"]
            )

            old_exact += int(old["exact"])
            candidate_exact += int(candidate["exact"])

            if old != candidate:
                print(
                    {
                        "family": family_id,
                        "variant": variant_index,
                        "old": old,
                        "candidate": candidate,
                    }
                )

    old_mean_precision = (
        old_total_precision / variants
    )

    candidate_mean_precision = (
        candidate_total_precision / variants
    )

    old_mean_recall = (
        old_total_recall / variants
    )

    candidate_mean_recall = (
        candidate_total_recall / variants
    )

    print(
        {
            "variants": variants,
            "old_mean_fact_precision": (
                old_mean_precision
            ),
            "candidate_mean_fact_precision": (
                candidate_mean_precision
            ),
            "old_mean_fact_recall": (
                old_mean_recall
            ),
            "candidate_mean_fact_recall": (
                candidate_mean_recall
            ),
            "old_exact_fact_sets": old_exact,
            "candidate_exact_fact_sets": candidate_exact,
            "old_exact_fact_rate": (
                old_exact / variants
            ),
            "candidate_exact_fact_rate": (
                candidate_exact / variants
            ),
        }
    )

    assert variants == 20

    assert (
        0.0 <= old_mean_precision <= 1.0
    )
    assert (
        0.0 <= candidate_mean_precision <= 1.0
    )

    assert (
        0.0 <= old_mean_recall <= 1.0
    )
    assert (
        0.0 <= candidate_mean_recall <= 1.0
    )