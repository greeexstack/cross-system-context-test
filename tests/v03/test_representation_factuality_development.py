from __future__ import annotations

from experiment.v03.evidence import EvidenceSemantics
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)

from test_extractor_paraphrases import PARAPHRASE_CASES


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
    required_features: dict[str, object],
) -> tuple[str, ...]:
    return tuple(
        field
        for field, expected in required_features.items()
        if expected is not None
    )


def _field_matches(
    actual: EvidenceSemantics,
    expected: dict[str, object],
) -> dict[str, bool]:
    fields = _explicit_fields(expected)

    return {
        field: getattr(actual, field) == expected[field]
        for field in fields
    }


def _measure() -> dict[str, object]:
    field_rows: list[dict[str, object]] = []
    pair_rows: list[dict[str, object]] = []

    total_decisions = 0
    matching_decisions = 0

    for (
        pair_id,
        original_text,
        paraphrase_text,
        required_features,
        _known_failure,
    ) in PARAPHRASE_CASES:

        original_actual = _extract(original_text)
        paraphrase_actual = _extract(paraphrase_text)

        original_matches = _field_matches(
            original_actual,
            required_features,
        )
        paraphrase_matches = _field_matches(
            paraphrase_actual,
            required_features,
        )

        for variant, actual, matches in (
            ("original", original_actual, original_matches),
            ("paraphrase", paraphrase_actual, paraphrase_matches),
        ):
            total_decisions += len(matches)
            matching_decisions += sum(matches.values())

            mismatches = tuple(
                field
                for field, matched in matches.items()
                if not matched
            )

            field_rows.append(
                {
                    "pair": pair_id,
                    "variant": variant,
                    "mismatches": mismatches,
                    "all_explicit_fields_correct": all(
                        matches.values()
                    ),
                }
            )

        explicit_fields = _explicit_fields(
            required_features,
        )

        original_projection = tuple(
            (field, getattr(original_actual, field))
            for field in explicit_fields
        )

        paraphrase_projection = tuple(
            (field, getattr(paraphrase_actual, field))
            for field in explicit_fields
        )

        expected_projection = tuple(
            (field, required_features[field])
            for field in explicit_fields
        )

        original_correct = (
            original_projection == expected_projection
        )
        paraphrase_correct = (
            paraphrase_projection == expected_projection
        )

        full_representation_changed = (
            original_actual != paraphrase_actual
        )

        explicit_projection_changed = (
            original_projection != paraphrase_projection
        )

        pair_rows.append(
            {
                "pair": pair_id,
                "full_representation_changed": (
                    full_representation_changed
                ),
                "explicit_projection_changed": (
                    explicit_projection_changed
                ),
                "original_factually_correct": original_correct,
                "paraphrase_factually_correct": paraphrase_correct,
                "benign_representation_drift": (
                    full_representation_changed
                    and original_correct
                    and paraphrase_correct
                    and not explicit_projection_changed
                ),
            }
        )

    return {
        "total_explicit_field_decisions": total_decisions,
        "matching_explicit_field_decisions": matching_decisions,
        "factual_field_accuracy": (
            matching_decisions / total_decisions
            if total_decisions
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