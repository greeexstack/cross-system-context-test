from __future__ import annotations

import re
from typing import List, Set, Tuple

from test_embedding_composition_interference import (
    COMPOSITION_INTERFERENCE_BATTERY,
    NEUTRAL_CONTROL,
)
from test_embedding_disentangled_generalization import (
    FACTS,
    _build_prototypes,
    _calibrate_thresholds,
    _predict,
)
from test_embedding_semantic_separation import MODEL


def _split_clauses(text: str) -> List[str]:
    """
    Structural diagnostic only.

    Split on the limited coordination/connective forms used by the
    independent composition battery. This does not add semantic rules.
    """
    parts = re.split(
        r"\s+(?:and|but|while)\s+|;\s*",
        text.strip(),
        flags=re.IGNORECASE,
    )

    clauses = [
        part.strip(" ,")
        for part in parts
        if part.strip(" ,")
    ]

    return clauses or [text.strip()]


def _predict_clausewise(
    text: str,
    prototypes,
    thresholds,
) -> Tuple[Set[str], List[dict]]:
    clauses = _split_clauses(text)

    all_facts: Set[str] = set()
    clause_results = []

    for clause in clauses:
        predicted, margins = _predict(
            clause,
            prototypes,
            thresholds,
        )

        all_facts.update(predicted)

        clause_results.append(
            {
                "clause": clause,
                "predicted": sorted(predicted),
                "margins": {
                    fact: round(margin, 4)
                    for fact, margin in margins.items()
                },
            }
        )

    return all_facts, clause_results


def test_clausewise_composition_interference() -> None:
    prototypes = _build_prototypes()
    thresholds = _calibrate_thresholds()

    total = 0
    exact = 0

    true_positive = 0
    false_positive = 0
    false_negative = 0

    existing_fact_preserved = 0
    existing_fact_tests = 0

    new_fact_recovered = 0
    new_fact_tests = 0

    print("\n=== CLAUSEWISE EMBEDDING COMPOSITION ===")

    for family_id, pair in COMPOSITION_INTERFERENCE_BATTERY:
        singleton_text, singleton_expected = pair[0]
        composed_text, composed_expected = pair[1]

        singleton_predicted, singleton_details = (
            _predict_clausewise(
                singleton_text,
                prototypes,
                thresholds,
            )
        )

        composed_predicted, composed_details = (
            _predict_clausewise(
                composed_text,
                prototypes,
                thresholds,
            )
        )

        composed_exact = (
            composed_predicted == composed_expected
        )

        total += 1
        exact += int(composed_exact)

        true_positive += len(
            composed_predicted & composed_expected
        )

        false_positive += len(
            composed_predicted - composed_expected
        )

        false_negative += len(
            composed_expected - composed_predicted
        )

        for fact in singleton_expected:
            existing_fact_tests += 1

            if (
                fact in singleton_predicted
                and fact in composed_predicted
            ):
                existing_fact_preserved += 1

        for fact in (
            composed_expected - singleton_expected
        ):
            new_fact_tests += 1

            if fact in composed_predicted:
                new_fact_recovered += 1

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
                "clauses": composed_details,
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

    print("\n=== CLAUSEWISE COMPOSITION SUMMARY ===")
    print(
        {
            "composed_exact": exact,
            "composed_total": total,
            "composed_accuracy": exact / total,
            "micro_precision": precision,
            "micro_recall": recall,
            "existing_fact_preservation": (
                existing_fact_preserved
                / existing_fact_tests
            ),
            "new_fact_recovery": (
                new_fact_recovered
                / new_fact_tests
            ),
        }
    )


def test_clausewise_vs_whole_sentence_on_same_cases() -> None:
    prototypes = _build_prototypes()
    thresholds = _calibrate_thresholds()

    print(
        "\n=== WHOLE-SENTENCE VS CLAUSEWISE "
        "COMPOSITION ==="
    )

    whole_exact = 0
    clausewise_exact = 0
    total = len(COMPOSITION_INTERFERENCE_BATTERY)

    for family_id, pair in COMPOSITION_INTERFERENCE_BATTERY:
        _singleton_text, _singleton_expected = pair[0]
        composed_text, expected = pair[1]

        whole_predicted, _ = _predict(
            composed_text,
            prototypes,
            thresholds,
        )

        clausewise_predicted, _details = (
            _predict_clausewise(
                composed_text,
                prototypes,
                thresholds,
            )
        )

        whole_is_exact = (
            whole_predicted == expected
        )
        clausewise_is_exact = (
            clausewise_predicted == expected
        )

        whole_exact += int(whole_is_exact)
        clausewise_exact += int(clausewise_is_exact)

        print(
            {
                "family": family_id,
                "expected": sorted(expected),
                "whole_sentence": sorted(
                    whole_predicted
                ),
                "clausewise": sorted(
                    clausewise_predicted
                ),
                "whole_exact": whole_is_exact,
                "clausewise_exact": clausewise_is_exact,
            }
        )

    print(
        {
            "total": total,
            "whole_sentence_exact": whole_exact,
            "whole_sentence_accuracy": (
                whole_exact / total
            ),
            "clausewise_exact": clausewise_exact,
            "clausewise_accuracy": (
                clausewise_exact / total
            ),
        }
    )


def test_clausewise_neutral_control() -> None:
    prototypes = _build_prototypes()
    thresholds = _calibrate_thresholds()

    correct = 0

    print("\n=== CLAUSEWISE NEUTRAL CONTROL ===")

    for index, text in enumerate(NEUTRAL_CONTROL):
        predicted, details = _predict_clausewise(
            text,
            prototypes,
            thresholds,
        )

        exact = predicted == set()

        if exact:
            correct += 1

        print(
            {
                "variant": index,
                "expected": [],
                "predicted": sorted(predicted),
                "exact": exact,
                "clauses": details,
            }
        )

    print(
        {
            "correct": correct,
            "total": len(NEUTRAL_CONTROL),
            "accuracy": correct / len(NEUTRAL_CONTROL),
        }
    )


def test_clausewise_splitter_is_deterministic() -> None:
    texts = [
        text
        for _family_id, pair in COMPOSITION_INTERFERENCE_BATTERY
        for text, _expected in pair
    ]

    for text in texts:
        assert _split_clauses(text) == _split_clauses(text)