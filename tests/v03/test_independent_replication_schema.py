from __future__ import annotations

from dataclasses import dataclass


SEMANTIC_FIELDS = frozenset(
    {
        "topic",
        "polarity",
        "negated_concepts",
        "requests_followup",
        "expresses_acceptance",
        "expresses_rejection",
        "confirms_approval",
        "confirms_completion",
        "requests_next_step",
        "concerns_same_work_item",
    }
)


@dataclass(frozen=True)
class IndependentReplicationCase:
    case_id: str
    primary_interpretation: str
    primary_decision_strength: str
    texts: tuple[str, ...]
    expected_fields: tuple[tuple[str, object], ...]


def validate_case(case: IndependentReplicationCase) -> None:
    assert case.case_id.strip()
    assert case.primary_interpretation.strip()
    assert case.primary_decision_strength.strip()
    assert len(case.texts) >= 2
    assert all(text.strip() for text in case.texts)

    seen: set[str] = set()

    for field, value in case.expected_fields:
        assert field in SEMANTIC_FIELDS
        assert field not in seen
        seen.add(field)

        if field == "topic":
            assert value is None or isinstance(value, str)
        elif field == "polarity":
            assert isinstance(value, str)
        elif field == "negated_concepts":
            assert isinstance(value, tuple)
        else:
            assert value is None or isinstance(value, bool)


def validate_suite(
    cases: tuple[IndependentReplicationCase, ...],
) -> None:
    assert cases
    case_ids = [case.case_id for case in cases]
    assert len(case_ids) == len(set(case_ids))

    for case in cases:
        validate_case(case)


def test_schema_accepts_a_minimal_generic_case() -> None:
    case = IndependentReplicationCase(
        case_id="example",
        primary_interpretation="opaque_primary_label",
        primary_decision_strength="moderate",
        texts=("first", "second"),
        expected_fields=(
            ("requests_followup", None),
        ),
    )

    validate_case(case)


def test_schema_rejects_unknown_semantic_fields() -> None:
    case = IndependentReplicationCase(
        case_id="example",
        primary_interpretation="opaque_primary_label",
        primary_decision_strength="moderate",
        texts=("first", "second"),
        expected_fields=(
            ("not_a_semantic_field", True),
        ),
    )

    try:
        validate_case(case)
    except AssertionError:
        return

    raise AssertionError("unknown semantic field was accepted")
