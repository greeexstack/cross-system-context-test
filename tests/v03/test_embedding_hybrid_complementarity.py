from __future__ import annotations

from typing import Dict

from test_embedding_fact_threshold_calibration import (
    _build_full_development_prototypes,
    _calibrate_thresholds,
    _predict_facts,
)
from test_embedding_semantic_separation import MODEL
from test_hybrid_complementarity_analysis import (
    _facts,
    V2,
    SPACY,
)
from test_hybrid_complementarity_battery import HYBRID_BATTERY


EMBEDDING = "embedding_fact_prototypes"


def _embedding_facts(
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

    predicted_facts, _margins = _predict_facts(
        embedding,
        prototypes,
        thresholds,
    )

    return predicted_facts


def test_three_way_error_overlap() -> None:
    prototypes = _build_full_development_prototypes()
    thresholds = _calibrate_thresholds()

    counts: Dict[str, int] = {
        "all_three_correct": 0,
        "embedding_v2_correct": 0,
        "embedding_spacy_correct": 0,
        "v2_spacy_correct": 0,
        "embedding_only_correct": 0,
        "v2_only_correct": 0,
        "spacy_only_correct": 0,
        "all_wrong": 0,
    }

    cases = []

    for family_id, variants in HYBRID_BATTERY:
        for variant_index, (text, expected_facts) in enumerate(
            variants,
            start=0,
        ):
            embedding_observed = _embedding_facts(
                text,
                prototypes,
                thresholds,
            )

            v2_observed = _facts(V2, text)
            spacy_observed = _facts(SPACY, text)

            embedding_correct = (
                embedding_observed == expected_facts
            )
            v2_correct = (
                v2_observed == expected_facts
            )
            spacy_correct = (
                spacy_observed == expected_facts
            )

            correct_count = sum(
                (
                    embedding_correct,
                    v2_correct,
                    spacy_correct,
                )
            )

            if correct_count == 3:
                category = "all_three_correct"
            elif (
                embedding_correct
                and v2_correct
                and not spacy_correct
            ):
                category = "embedding_v2_correct"
            elif (
                embedding_correct
                and spacy_correct
                and not v2_correct
            ):
                category = "embedding_spacy_correct"
            elif (
                v2_correct
                and spacy_correct
                and not embedding_correct
            ):
                category = "v2_spacy_correct"
            elif (
                embedding_correct
                and not v2_correct
                and not spacy_correct
            ):
                category = "embedding_only_correct"
            elif (
                v2_correct
                and not embedding_correct
                and not spacy_correct
            ):
                category = "v2_only_correct"
            elif (
                spacy_correct
                and not embedding_correct
                and not v2_correct
            ):
                category = "spacy_only_correct"
            else:
                category = "all_wrong"

            counts[category] += 1

            case = {
                "family": family_id,
                "variant": variant_index,
                "expected": sorted(expected_facts),
                "embedding": sorted(embedding_observed),
                "v2": sorted(v2_observed),
                "spacy": sorted(spacy_observed),
                "category": category,
            }

            cases.append(case)
            print(case)

    print("\n=== THREE-WAY EXTRACTOR ERROR OVERLAP ===")
    print(counts)

    assert sum(counts.values()) == 16


def test_three_way_recoverability_upper_bound() -> None:
    prototypes = _build_full_development_prototypes()
    thresholds = _calibrate_thresholds()

    recoverable_by_any = 0
    all_wrong = 0

    for _family_id, variants in HYBRID_BATTERY:
        for text, expected_facts in variants:
            embedding = _embedding_facts(
                text,
                prototypes,
                thresholds,
            )

            v2 = _facts(V2, text)
            spacy = _facts(SPACY, text)

            embedding_correct = (
                embedding == expected_facts
            )
            v2_correct = v2 == expected_facts
            spacy_correct = spacy == expected_facts

            if (
                embedding_correct
                or v2_correct
                or spacy_correct
            ):
                recoverable_by_any += 1
            else:
                all_wrong += 1

    print("\n=== THREE-WAY RECOVERABILITY UPPER BOUND ===")
    print(
        {
            "total": 16,
            "recoverable_by_any": recoverable_by_any,
            "all_three_wrong": all_wrong,
            "upper_bound": recoverable_by_any / 16,
        }
    )

    assert recoverable_by_any + all_wrong == 16


def test_three_way_family_overlap() -> None:
    prototypes = _build_full_development_prototypes()
    thresholds = _calibrate_thresholds()

    print("\n=== THREE-WAY FAMILY OVERLAP ===")

    for family_id, variants in HYBRID_BATTERY:
        counts = {
            "all_three_correct": 0,
            "embedding_v2_correct": 0,
            "embedding_spacy_correct": 0,
            "v2_spacy_correct": 0,
            "embedding_only_correct": 0,
            "v2_only_correct": 0,
            "spacy_only_correct": 0,
            "all_wrong": 0,
        }

        for text, expected_facts in variants:
            embedding = _embedding_facts(
                text,
                prototypes,
                thresholds,
            )

            v2 = _facts(V2, text)
            spacy = _facts(SPACY, text)

            embedding_correct = (
                embedding == expected_facts
            )
            v2_correct = v2 == expected_facts
            spacy_correct = spacy == expected_facts

            correct_count = sum(
                (
                    embedding_correct,
                    v2_correct,
                    spacy_correct,
                )
            )

            if correct_count == 3:
                category = "all_three_correct"
            elif (
                embedding_correct
                and v2_correct
                and not spacy_correct
            ):
                category = "embedding_v2_correct"
            elif (
                embedding_correct
                and spacy_correct
                and not v2_correct
            ):
                category = "embedding_spacy_correct"
            elif (
                v2_correct
                and spacy_correct
                and not embedding_correct
            ):
                category = "v2_spacy_correct"
            elif (
                embedding_correct
                and not v2_correct
                and not spacy_correct
            ):
                category = "embedding_only_correct"
            elif (
                v2_correct
                and not embedding_correct
                and not spacy_correct
            ):
                category = "v2_only_correct"
            elif (
                spacy_correct
                and not embedding_correct
                and not v2_correct
            ):
                category = "spacy_only_correct"
            else:
                category = "all_wrong"

            counts[category] += 1

        print(
            {
                "family": family_id,
                **counts,
            }
        )

        assert sum(counts.values()) == 4


def test_embedding_hybrid_determinism() -> None:
    prototypes = _build_full_development_prototypes()
    thresholds = _calibrate_thresholds()

    first = []
    second = []

    for _family_id, variants in HYBRID_BATTERY:
        for text, _expected_facts in variants:
            first.append(
                sorted(
                    _embedding_facts(
                        text,
                        prototypes,
                        thresholds,
                    )
                )
            )

            second.append(
                sorted(
                    _embedding_facts(
                        text,
                        prototypes,
                        thresholds,
                    )
                )
            )

    assert first == second