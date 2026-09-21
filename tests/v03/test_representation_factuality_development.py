from __future__ import annotations

from experiment.v03.evidence import EvidenceSemantics
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)

from fixtures.semantic_cases import (
    F01_EQUIVALENT_A,
    F01_EQUIVALENT_B,
    F02_EQUIVALENT_A,
    F02_EQUIVALENT_B,
    F03_EQUIVALENT_A,
    F03_EQUIVALENT_B,
    F10_EQUIVALENT_A,
    F10_EQUIVALENT_B,
)


FIELDS = (
    "topic",
    "requests_followup",
    "confirms_approval",
    "expresses_acceptance",
    "expresses_rejection",
    "confirms_completion",
    "requests_next_step",
    "concerns_same_work_item",
)


PAIRS = (
    ("F01", F01_EQUIVALENT_A, F01_EQUIVALENT_B),
    ("F02", F02_EQUIVALENT_A, F02_EQUIVALENT_B),
    ("F03", F03_EQUIVALENT_A, F03_EQUIVALENT_B),
    ("F10", F10_EQUIVALENT_A, F10_EQUIVALENT_B),
)


EXTRACTOR = LexicalNormalizationSemanticExtractor()


def _extract(text: str) -> EvidenceSemantics:
    return EXTRACTOR.extract(
        evidence_id="FACTUALITY",
        content=text,
        source_system="representation_factuality",
        record_id="FACTUALITY",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="FACTUALITY-CUSTOMER",
    ).evidence.semantics


def _explicit_fields(
    expected: EvidenceSemantics,
) -> tuple[str, ...]:
    return tuple(
        field
        for field in FIELDS
        if getattr(expected, field) is not None
    )


def _field_matches(
    actual: EvidenceSemantics,
    expected: EvidenceSemantics,
) -> dict[str, bool]:
    return {
        field: getattr(actual, field) == getattr(expected, field)
        for field in _explicit_fields(expected)
    }


def _measure() -> dict[str, object]:
    field_rows: list[dict[str, object]] = []
    pair_rows: list[dict[str, object]] = []

    total_fields = 0
    matching_fields = 0

    for family_id, left, right in PAIRS:
        left_actual = _extract(left.content)
        right_actual = _extract(right.content)

        left_matches = _field_matches(
            left_actual,
            left.semantics,
        )
        right_matches = _field_matches(
            right_actual,
            right.semantics,
        )

        for variant, actual, expected, matches in (
            ("A", left_actual, left.semantics, left_matches),
            ("B", right_actual, right.semantics, right_matches),
        ):
            total_fields += len(matches)
            matching_fields += sum(matches.values())

            mismatches = tuple(
                field
                for field, matched in matches.items()
                if not matched
            )

            field_rows.append(
                {
                    "family": family_id,
                    "variant": variant,
                    "mismatches": mismatches,
                    "all_explicit_fields_correct": all(
                        matches.values()
                    ),
                }
            )

        explicit = _explicit_fields(left.semantics)

        left_projection = tuple(
            (field, getattr(left_actual, field))
            for field in explicit
        )

        right_projection = tuple(
            (field, getattr(right_actual, field))
            for field in explicit
        )

        expected_projection = tuple(
            (field, getattr(left.semantics, field))
            for field in explicit
        )

        full_representation_changed = (
            left_actual != right_actual
        )

        projected_representation_changed = (
            left_projection != right_projection
        )

        left_factual = left_projection == expected_projection
        right_factual = right_projection == expected_projection

        pair_rows.append(
            {
                "family": family_id,
                "full_representation_changed": (
                    full_representation_changed
                ),
                "explicit_projection_changed": (
                    projected_representation_changed
                ),
                "left_factually_correct": left_factual,
                "right_factually_correct": right_factual,
                "benign_representation_drift": (
                    full_representation_changed
                    and left_factual
                    and right_factual
                    and not projected_representation_changed
                ),
            }
        )

    return {
        "total_explicit_field_decisions": total_fields,
        "matching_explicit_field_decisions": matching_fields,
        "factual_field_accuracy": (
            matching_fields / total_fields
            if total_fields
            else 0.0
        ),
        "field_rows": field_rows,
        "pair_rows": pair_rows,
    }


def test_development_representation_factuality() -> None:
    result = _measure()

    print("\n=== DEVELOPMENT REPRESENTATION FACTUALITY ===")
    print(
        {
            key: value
            for key, value in result.items()
            if key not in {"field_rows", "pair_rows"}
        }
    )

    print("\nFIELD RESULTS")
    for row in result["field_rows"]:
        print(row)

    print("\nPAIR RESULTS")
    for row in result["pair_rows"]:
        print(row)

    assert result["total_explicit_field_decisions"] > 0
    assert 0.0 <= result["factual_field_accuracy"] <= 1.0


def test_development_representation_factuality_is_deterministic() -> None:
    assert _measure() == _measure()