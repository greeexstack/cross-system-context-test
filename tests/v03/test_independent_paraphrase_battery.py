"""
Independent v0.3 paraphrase battery.

Purpose
-------
Measure behavioral consistency under independently authored,
semantics-preserving wording changes.

This battery is intentionally outside the frozen v0.2 fixtures and does
not import expected transition labels or ground truth into the engine.

The engine receives only:
    - the fixed primary state
    - the natural-language evidence
    - fixed structured metadata

For each family:
    original wording
        vs.
    independently authored paraphrases

Primary metric
--------------
Paraphrase Behavioral Consistency (PBC):

    pair_consistent = 1
        when paraphrase behavior equals original behavior

    pair_consistent = 0
        when paraphrase behavior differs from original behavior

This is a measurement experiment, not an acceptance gate for a redesigned
engine.

No production code is changed.
"""

from __future__ import annotations

import json
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

FIXED_TIMESTAMP = "2026-09-12T10:00:00Z"
FIXED_CUSTOMER_ID = "INDEPENDENT-CUSTOMER"
FIXED_SOURCE = "independent_paraphrase_battery"
FIXED_RECORD_ID = "INDEPENDENT-PARAPHRASE"


# These texts are independently authored for this experiment.
#
# They deliberately do not copy the wording from:
#     docs/v03-paraphrase-battery.md
#     tests/v03/test_extractor_paraphrases.py
#     tests/v03/test_end_to_end_paraphrase.py
#
# The semantic situation is held constant within each family.
BATTERY = (
    (
        "R1-relevant",
        PrimaryState("quote_pending_decision"),
        (
            "The buyer is reviewing the proposal and asked us to "
            "reconnect next Thursday.",
            "The customer is still examining the offer and suggested "
            "another conversation next Thursday.",
            "The proposal remains under review, and the buyer requested "
            "a call again next Thursday.",
            "The client is considering the quoted plan and wants to "
            "speak again next Thursday.",
        ),
    ),
    (
        "R2-supporting",
        PrimaryState("quote_pending_decision"),
        (
            "The quoted price fits the approved budget, and purchasing "
            "has started its internal review.",
            "The proposed amount is covered by the customer's budget, "
            "while procurement has begun its review.",
            "Funding for the quoted sum is authorized, and the purchasing "
            "team is now processing the proposal.",
            "The customer has budget clearance for this quote and says "
            "the buying process is underway.",
        ),
    ),
    (
        "R3-contradictory",
        PrimaryState("negotiation_open"),
        (
            "The buyer says the amended terms are unacceptable and wants "
            "the offer reworked.",
            "The customer will not accept the revised conditions and has "
            "asked for a new version of the proposal.",
            "The updated commercial arrangement does not meet the buyer's "
            "needs, so they want the proposal reconsidered.",
            "The client rejected the changed terms and requested another "
            "pass on the offer.",
        ),
    ),
    (
        "R4-irrelevant",
        PrimaryState("quote_pending_decision"),
        (
            "The customer is discussing a different branch expansion and "
            "gives no update on the quoted opportunity.",
            "The conversation is about another location rollout, with "
            "nothing said about the current proposal.",
            "The buyer raised a separate expansion project and provided "
            "no information on this quote.",
            "This exchange concerns a different deployment and does not "
            "address the opportunity under review.",
        ),
    ),
    (
        "R5-service-next-step",
        PrimaryState("service_completed_next_step_unrecorded"),
        (
            "The implementation workshop is complete, and the customer "
            "asks what comes next in the handoff.",
            "The rollout session has finished and the customer wants to "
            "know the next handover step.",
            "The implementation meeting is over, and the client is asking "
            "about the following transition stage.",
            "The workshop has concluded, and the customer would like "
            "guidance on the next handoff.",
        ),
    ),
)


def _evaluate(
    primary: PrimaryState,
    text: str,
):
    extractor = LexicalNormalizationSemanticExtractor()

    extracted = extractor.extract(
        evidence_id=FIXED_RECORD_ID,
        content=text,
        source_system=FIXED_SOURCE,
        record_id=FIXED_RECORD_ID,
        occurred_at=FIXED_TIMESTAMP,
        customer_id=FIXED_CUSTOMER_ID,
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

    return reasoner.evaluate(
        primary,
        condition,
    )


def _observable_state(result) -> tuple:
    """
    Behavioral state used for comparison.

    We deliberately exclude explanatory prose so that wording differences
    in diagnostic text do not count as behavioral changes.
    """
    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


def _case_result(
    family_id: str,
    primary: PrimaryState,
    texts: tuple[str, ...],
) -> dict:
    results = [
        _evaluate(primary, text)
        for text in texts
    ]

    states = [
        _observable_state(result)
        for result in results
    ]

    original_state = states[0]

    pair_results = [
        {
            "variant_index": index,
            "behaviorally_consistent": (
                state == original_state
            ),
            "original_state": original_state,
            "variant_state": state,
        }
        for index, state in enumerate(
            states[1:],
            start=1,
        )
    ]

    return {
        "family_id": family_id,
        "pair_count": len(pair_results),
        "consistent_pair_count": sum(
            pair["behaviorally_consistent"]
            for pair in pair_results
        ),
        "inconsistent_pair_count": sum(
            not pair["behaviorally_consistent"]
            for pair in pair_results
        ),
        "all_variants_consistent": all(
            pair["behaviorally_consistent"]
            for pair in pair_results
        ),
        "original_state": original_state,
        "variant_states": states[1:],
        "pair_results": pair_results,
    }


def _run_battery() -> list[dict]:
    records = []

    for family_id, primary, texts in BATTERY:
        records.append(
            _case_result(
                family_id,
                primary,
                texts,
            )
        )

    return records


def test_battery_shape_is_controlled() -> None:
    assert len(BATTERY) == 5

    for family_id, _primary, texts in BATTERY:
        assert family_id.startswith("R")
        assert len(texts) == 4

        assert all(
            isinstance(text, str) and text.strip()
            for text in texts
        )

        # Same fixed metadata are used by every member of the family.
        extractor = LexicalNormalizationSemanticExtractor()

        extracted = [
            extractor.extract(
                evidence_id=FIXED_RECORD_ID,
                content=text,
                source_system=FIXED_SOURCE,
                record_id=FIXED_RECORD_ID,
                occurred_at=FIXED_TIMESTAMP,
                customer_id=FIXED_CUSTOMER_ID,
            ).evidence
            for text in texts
        ]

        assert all(
            item.provenance.source_system == FIXED_SOURCE
            for item in extracted
        )

        assert all(
            item.provenance.record_id == FIXED_RECORD_ID
            for item in extracted
        )

        assert all(
            item.identity.customer_id == FIXED_CUSTOMER_ID
            for item in extracted
        )

        assert len(
            {item.timestamp for item in extracted}
        ) == 1


def test_original_behavior_is_reproducible() -> None:
    for family_id, primary, texts in BATTERY:
        first = _observable_state(
            _evaluate(primary, texts[0])
        )
        second = _observable_state(
            _evaluate(primary, texts[0])
        )

        assert first == second, (
            f"{family_id}: original wording was not reproducible\n"
            f"first={first}\n"
            f"second={second}"
        )


def test_independent_battery_reports_paraphrase_behavior() -> None:
    records = _run_battery()

    total_pairs = sum(
        record["pair_count"]
        for record in records
    )

    consistent_pairs = sum(
        record["consistent_pair_count"]
        for record in records
    )

    inconsistent_pairs = sum(
        record["inconsistent_pair_count"]
        for record in records
    )

    pbc = (
        consistent_pairs / total_pairs
        if total_pairs
        else 0.0
    )

    print(
        "\n=== INDEPENDENT PARAPHRASE BATTERY ==="
    )

    print(
        json.dumps(
            {
                "families": len(records),
                "pairs": total_pairs,
                "behaviorally_consistent_pairs": (
                    consistent_pairs
                ),
                "behaviorally_inconsistent_pairs": (
                    inconsistent_pairs
                ),
                "paraphrase_behavioral_consistency": pbc,
            },
            indent=2,
            sort_keys=True,
        )
    )

    for record in records:
        print(
            json.dumps(
                record,
                indent=2,
                sort_keys=True,
            )
        )

    # Measurement-phase invariants only.
    # No outcome is asserted as a success/failure threshold yet.
    assert total_pairs == 15
    assert (
        consistent_pairs + inconsistent_pairs
        == total_pairs
    )
    assert (
        0.0 <= pbc <= 1.0
    )


def test_negative_control_is_measured_separately() -> None:
    irrelevant = next(
        item
        for item in BATTERY
        if item[0] == "R4-irrelevant"
    )

    family_id, primary, texts = irrelevant

    record = _case_result(
        family_id,
        primary,
        texts,
    )

    print(
        "\n=== NEGATIVE CONTROL: R4 ==="
    )
    print(
        json.dumps(
            record,
            indent=2,
            sort_keys=True,
        )
    )

    assert record["pair_count"] == 3
    assert (
        0
        <= record["consistent_pair_count"]
        <= 3
    )
    assert (
        0
        <= record["inconsistent_pair_count"]
        <= 3
    )


@pytest.mark.parametrize(
    "family_id,primary,texts",
    BATTERY,
)
def test_each_independent_family_has_three_controlled_pairs(
    family_id: str,
    primary: PrimaryState,
    texts: tuple[str, ...],
) -> None:
    record = _case_result(
        family_id,
        primary,
        texts,
    )

    assert record["pair_count"] == 3

    assert (
        record["consistent_pair_count"]
        + record["inconsistent_pair_count"]
        == 3
    )

    for pair in record["pair_results"]:
        assert pair["variant_index"] in (1, 2, 3)
        assert isinstance(
            pair["behaviorally_consistent"],
            bool,
        )