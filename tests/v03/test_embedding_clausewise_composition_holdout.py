from __future__ import annotations

from typing import Dict

from test_embedding_clausewise_composition import (
    _predict_clausewise,
)
from test_embedding_clausewise_composition_holdout_battery import (
    CLAUSEWISE_COMPOSITION_HOLDOUT,
)
from test_embedding_disentangled_generalization import (
    _build_prototypes,
    _calibrate_thresholds,
)
from test_embedding_semantic_separation import MODEL


def _whole_sentence_predict(
    text: str,
    prototypes,
    thresholds,
) -> set[str]:
    from test_embedding_disentangled_generalization import (
        _predict,
    )

    predicted, _margins = _predict(
        text,
        prototypes,
        thresholds,
    )

    return predicted


def test_fresh_composition_holdout_whole_vs_clausewise() -> None:
    prototypes = _build_prototypes()
    thresholds = _calibrate_thresholds()

    print(
        "\n=== FRESH COMPOSITION HOLDOUT: "
        "WHOLE SENTENCE VS CLAUSEWISE ==="
    )

    whole_exact = 0
    clausewise_exact = 0
    total = 0

    family_results: Dict[str, dict[str, int]] = {}

    for family_id, variants in CLAUSEWISE_COMPOSITION_HOLDOUT:
        family_total = 0
        family_whole = 0
        family_clausewise = 0

        for variant_index, (text, expected) in enumerate(
            variants,
            start=0,
        ):
            whole = _whole_sentence_predict(
                text,
                prototypes,
                thresholds,
            )

            clausewise, details = _predict_clausewise(
                text,
                prototypes,
                thresholds,
            )

            whole_correct = whole == expected
            clausewise_correct = clausewise == expected

            total += 1
            family_total += 1

            if whole_correct:
                whole_exact += 1
                family_whole += 1

            if clausewise_correct:
                clausewise_exact += 1
                family_clausewise += 1

            print(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "expected": sorted(expected),
                    "whole_sentence": sorted(whole),
                    "clausewise": sorted(clausewise),
                    "whole_exact": whole_correct,
                    "clausewise_exact": clausewise_correct,
                    "clauses": details,
                    "text": text,
                }
            )

        family_results[family_id] = {
            "whole_exact": family_whole,
            "clausewise_exact": family_clausewise,
            "total": family_total,
        }

    print("\n=== FRESH COMPOSITION HOLDOUT SUMMARY ===")
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
            "absolute_improvement": (
                (clausewise_exact - whole_exact)
                / total
            ),
        }
    )

    print("\n=== FAMILY BREAKDOWN ===")

    for family_id, result in family_results.items():
        print(
            {
                "family": family_id,
                **result,
            }
        )


def test_fresh_holdout_clausewise_construction_breakdown() -> None:
    prototypes = _build_prototypes()
    thresholds = _calibrate_thresholds()

    print(
        "\n=== CLAUSEWISE FRESH HOLDOUT "
        "CONSTRUCTION BREAKDOWN ==="
    )

    construction_groups = {
        "semicolon": [],
        "and": [],
        "while": [],
        "after": [],
        "although": [],
        "with": [],
        "once": [],
    }

    for _family_id, variants in CLAUSEWISE_COMPOSITION_HOLDOUT:
        for text, expected in variants:
            lower = text.lower()

            if ";" in text:
                group = "semicolon"
            elif ", and " in lower:
                group = "and"
            elif ", while " in lower:
                group = "while"
            elif lower.startswith("after "):
                group = "after"
            elif lower.startswith("although "):
                group = "although"
            elif lower.startswith("with "):
                group = "with"
            elif lower.startswith("once "):
                group = "once"
            else:
                raise AssertionError(
                    f"Unclassified construction: {text}"
                )

            construction_groups[group].append(
                (text, expected)
            )

    for group, cases in construction_groups.items():
        whole_correct = 0
        clausewise_correct = 0

        for text, expected in cases:
            whole = _whole_sentence_predict(
                text,
                prototypes,
                thresholds,
            )

            clausewise, _details = _predict_clausewise(
                text,
                prototypes,
                thresholds,
            )

            whole_correct += int(
                whole == expected
            )

            clausewise_correct += int(
                clausewise == expected
            )

        print(
            {
                "construction": group,
                "total": len(cases),
                "whole_sentence_correct": whole_correct,
                "clausewise_correct": clausewise_correct,
                "whole_sentence_accuracy": (
                    whole_correct / len(cases)
                ),
                "clausewise_accuracy": (
                    clausewise_correct / len(cases)
                ),
            }
        )


def test_fresh_holdout_clausewise_is_deterministic() -> None:
    prototypes = _build_prototypes()
    thresholds = _calibrate_thresholds()

    first = []
    second = []

    for _family_id, variants in CLAUSEWISE_COMPOSITION_HOLDOUT:
        for text, _expected in variants:
            first.append(
                _predict_clausewise(
                    text,
                    prototypes,
                    thresholds,
                )
            )

            second.append(
                _predict_clausewise(
                    text,
                    prototypes,
                    thresholds,
                )
            )

    assert first == second