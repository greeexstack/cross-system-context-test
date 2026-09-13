from __future__ import annotations

from datetime import datetime, timezone

import pytest

from experiment.v03.evidence import EvidenceCondition
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)


EVALUATION_AT = datetime(
    2026,
    9,
    13,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


CASES = (
    (
        "F01",
        PrimaryState("quote_pending_decision"),
        (
            "The customer is assessing the proposal and would like "
            "another discussion next week.",
        ),
        {
            "interpretation_class": "quote_followup_pending",
            "support_level": "supported_by_secondary_context",
        },
    ),
    (
        "F02",
        PrimaryState("quote_pending_decision"),
        (
            "The customer has budget approval for the quoted amount "
            "and says procurement is progressing.",
        ),
        {
            "interpretation_class": "quote_pending_decision",
            "support_level": "secondary_supported",
            "decision_strength": "stronger",
        },
    ),
    (
        "F03",
        PrimaryState("negotiation_open"),
        (
            "The customer says the revised commercial terms are "
            "unacceptable and wants the proposal reconsidered.",
        ),
        {
            "interpretation_class": "negotiation_open",
            "support_level": "weakened_by_secondary_context",
            "decision_strength": "weaker",
        },
    ),
    (
        "F04",
        PrimaryState("quote_pending_decision"),
        (
            "The customer is discussing a different store rollout "
            "and says nothing about this quoted opportunity.",
        ),
        {
            "interpretation_class": "quote_pending_decision",
            "support_level": "primary_only",
        },
    ),
    (
        "F10",
        PrimaryState("service_completed_next_step_unrecorded"),
        (
            "The customer confirms the migration workshop is finished "
            "and asks what happens in the following handoff.",
        ),
        {
            "interpretation_class": "service_completed_next_step_unrecorded",
            "support_level": "supported_by_secondary_context",
            "recommended_focus": "next_step_followup",
        },
    ),
)


def _evaluate(
    primary: PrimaryState,
    text: str,
):
    extractor = LexicalNormalizationSemanticExtractor()

    extracted = extractor.extract(
        evidence_id="DIAGNOSTIC",
        content=text,
        source_system="diagnostic",
        record_id="DIAGNOSTIC",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
    )

    condition = EvidenceCondition(
        availability="available",
        items=(extracted.evidence,),
    )

    reasoner = V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )

    return reasoner.evaluate(primary, condition)


@pytest.mark.parametrize(
    "case_id,primary,texts,expected",
    CASES,
)
def test_candidate_extraction_drives_expected_transition(
    case_id: str,
    primary: PrimaryState,
    texts: tuple[str, ...],
    expected: dict[str, str],
) -> None:
    for text in texts:
        result = _evaluate(primary, text)

        for field, expected_value in expected.items():
            actual_value = getattr(result, field)

            assert actual_value == expected_value, (
                f"{case_id}: {field} mismatch\n"
                f"expected={expected_value!r}\n"
                f"actual={actual_value!r}\n"
                f"text={text!r}"
            )