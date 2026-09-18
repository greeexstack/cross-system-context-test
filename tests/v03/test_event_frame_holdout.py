from __future__ import annotations

from experiment.v03.event_frame_adapter import frames_to_semantics
from experiment.v03.event_frames import (
    CanonicalEventFrameExtractor,
)
from experiment.v03.evidence import (
    EvidenceCondition,
    EvidenceIdentity,
    EvidenceProvenance,
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)

from test_independent_paraphrase_battery import (
    EVALUATION_AT,
)


HOLDOUT = (
    (
        "H1-followup",
        PrimaryState("quote_pending_decision"),
        (
            "The purchaser is weighing the offer and asked us to "
            "reconnect on Thursday.",
            "The buyer is examining the quotation and wants to "
            "talk again Thursday.",
            "The proposal remains with the buyer, who would welcome "
            "a catch-up on Thursday.",
            "The client is considering the quoted plan and suggested "
            "a call for Thursday.",
        ),
        {
            "followup_request",
        },
    ),
    (
        "H2-supporting",
        PrimaryState("quote_pending_decision"),
        (
            "Finance has sanctioned the quoted sum, and sourcing has "
            "opened its review.",
            "The bid amount is cleared under budget, while the "
            "purchasing team has begun work.",
            "Funding for the proposed figure has received authorization, "
            "and procurement is moving ahead.",
            "The quote sits within approved funding, with buying now "
            "under way.",
        ),
        {
            "budget_approved",
            "procurement_progressing",
        },
    ),
    (
        "H3-contradictory",
        PrimaryState("negotiation_open"),
        (
            "The amended commercial arrangement falls short of the "
            "buyer's needs, so the offer must be reconsidered.",
            "The revised deal is unacceptable to the buyer, who wants "
            "the proposal reopened.",
            "The buyer declines the revised terms and asks for another "
            "version.",
            "The client will not accept the changed conditions and "
            "has requested a fresh proposal.",
        ),
        {
            "commercial_terms_rejected",
        },
    ),
    (
        "H4-irrelevant",
        PrimaryState("quote_pending_decision"),
        (
            "The conversation is about another regional rollout and "
            "contains no details about the current quote.",
            "The customer is focused on a separate installation and "
            "says nothing about the present proposal.",
            "The exchange concerns another branch deployment, with "
            "no update on this opportunity.",
            "The buyer discussed an unrelated site launch and did not "
            "address this quote.",
        ),
        {
            "different_work_item",
        },
    ),
    (
        "H5-service-next-step",
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        (
            "The implementation workshop has wrapped up, and the "
            "client asks about the next transfer.",
            "The deployment session is finished, and the customer wants "
            "guidance on the subsequent handoff.",
            "The rollout meeting has concluded and the customer wants "
            "to know what follows in the transfer.",
            "The migration clinic is done; the client asks about the "
            "ensuing handover.",
        ),
        {
            "service_completed",
            "next_step_requested",
        },
    ),
)


def _extract(text: str):
    return CanonicalEventFrameExtractor().extract(
        content=text,
    )


def _core_facts(frames) -> set[str]:
    facts: set[str] = set()

    for frame in frames:
        if (
            frame.action == "request"
            and frame.object == "followup_conversation"
            and frame.state == "requested"
        ):
            facts.add("followup_request")

        if (
            frame.action == "confirm"
            and frame.object == "quote"
            and frame.state == "budget_approved"
        ):
            facts.add("budget_approved")

        if (
            frame.action == "report"
            and frame.object == "procurement"
            and frame.state == "progressing"
        ):
            facts.add("procurement_progressing")

        if (
            frame.action == "accept"
            and frame.object == "commercial_terms"
            and frame.state == "rejected"
        ):
            facts.add("commercial_terms_rejected")

        if (
            frame.action == "confirm"
            and frame.object == "service"
            and frame.state == "completed"
        ):
            facts.add("service_completed")

        if (
            frame.action == "request"
            and frame.object in {"handoff", "next_step"}
            and frame.state == "next_step"
        ):
            facts.add("next_step_requested")

        if frame.relevance == "different_work_item":
            facts.add("different_work_item")

    return facts


def _behavior(
    primary: PrimaryState,
    text: str,
) -> tuple:
    extracted = _extract(text)

    semantics = frames_to_semantics(
        extracted.frames,
    )

    evidence = SemanticEvidence(
        evidence_id="HOLDOUT",
        content=text,
        provenance=EvidenceProvenance(
            source_system="event_frame_holdout",
            record_id="HOLDOUT",
            occurred_at=__import__(
                "datetime"
            ).datetime.fromisoformat(
                "2026-09-12T10:00:00+00:00"
            ),
        ),
        identity=EvidenceIdentity(
            customer_id="HOLDOUT-CUSTOMER",
            quality=IdentityQuality.CONFIRMED,
        ),
        semantics=semantics,
    )

    condition = EvidenceCondition(
        availability="available",
        items=(evidence,),
    )

    result = V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    ).evaluate(
        primary,
        condition,
    )

    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


def test_holdout_shape_is_fixed() -> None:
    assert len(HOLDOUT) == 5

    for family_id, _primary, texts, expected_facts in HOLDOUT:
        assert family_id.startswith("H")
        assert len(texts) == 4
        assert expected_facts


def test_unseen_holdout_core_fact_recall_is_measured() -> None:
    total_variants = 0
    complete_variants = 0
    partial_variants = 0
    missed_variants = 0

    print(
        "\n=== UNSEEN HOLDOUT CORE-FACT RECALL ==="
    )

    for family_id, _primary, texts, expected_facts in HOLDOUT:
        for variant_index, text in enumerate(
            texts,
            start=0,
        ):
            observed = _core_facts(
                _extract(text).frames
            )

            total_variants += 1

            if expected_facts.issubset(observed):
                complete_variants += 1
            elif observed.intersection(expected_facts):
                partial_variants += 1
            else:
                missed_variants += 1

            print(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "expected": sorted(expected_facts),
                    "observed": sorted(observed),
                    "complete": expected_facts.issubset(
                        observed
                    ),
                }
            )

    print(
        {
            "total_variants": total_variants,
            "complete_variants": complete_variants,
            "partial_variants": partial_variants,
            "missed_variants": missed_variants,
            "complete_recall_rate": (
                complete_variants
                / total_variants
            ),
        }
    )

    assert total_variants == 20
    assert (
        complete_variants
        + partial_variants
        + missed_variants
        == total_variants
    )


def test_unseen_holdout_behavioral_consistency_is_measured() -> None:
    total_pairs = 0
    consistent_pairs = 0
    inconsistent_pairs = 0

    print(
        "\n=== UNSEEN HOLDOUT BEHAVIOR ==="
    )

    for family_id, primary, texts, _expected_facts in HOLDOUT:
        original = _behavior(
            primary,
            texts[0],
        )

        for variant_index, text in enumerate(
            texts[1:],
            start=1,
        ):
            total_pairs += 1

            variant = _behavior(
                primary,
                text,
            )

            consistent = variant == original

            if consistent:
                consistent_pairs += 1
            else:
                inconsistent_pairs += 1

            print(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "consistent": consistent,
                    "original": original,
                    "variant_state": variant,
                }
            )

    print(
        {
            "total_pairs": total_pairs,
            "consistent_pairs": consistent_pairs,
            "inconsistent_pairs": inconsistent_pairs,
            "behavioral_consistency_rate": (
                consistent_pairs
                / total_pairs
            ),
        }
    )

    assert total_pairs == 15
    assert (
        consistent_pairs
        + inconsistent_pairs
        == total_pairs
    )


def test_unseen_holdout_negative_control_is_measured() -> None:
    family = next(
        item
        for item in HOLDOUT
        if item[0] == "H4-irrelevant"
    )

    _family_id, primary, texts, _expected_facts = family

    states = [
        _behavior(
            primary,
            text,
        )
        for text in texts
    ]

    consistent = sum(
        state == states[0]
        for state in states[1:]
    )

    print(
        "\n=== UNSEEN HOLDOUT NEGATIVE CONTROL ==="
    )
    print(
        {
            "pairs": 3,
            "consistent_pairs": consistent,
            "consistency_rate": (
                consistent / 3
            ),
        }
    )

    assert 0 <= consistent <= 3