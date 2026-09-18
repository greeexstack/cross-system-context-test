from __future__ import annotations

from experiment.v03.event_frames import (
    CanonicalEventFrameExtractor,
)


CORE_FACTS = (
    (
        "R1-relevant",
        (
            "followup_request",
        ),
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
        (
            "budget_approved",
            "procurement_progressing",
        ),
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
        (
            "commercial_terms_rejected",
        ),
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
        (
            "different_work_item",
        ),
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
        (
            "service_completed",
            "next_step_requested",
        ),
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


def _frames(text: str):
    return CanonicalEventFrameExtractor().extract(
        content=text,
    ).frames


def _has_frame(
    frames,
    *,
    action: str,
    object: str | None = None,
    state: str | None = None,
    relevance: str | None = None,
) -> bool:
    return any(
        frame.action == action
        and (
            object is None
            or frame.object == object
        )
        and (
            state is None
            or frame.state == state
        )
        and (
            relevance is None
            or frame.relevance == relevance
        )
        for frame in frames
    )


def _core_facts(frames) -> set[str]:
    facts: set[str] = set()

    if _has_frame(
        frames,
        action="request",
        object="followup_conversation",
        state="requested",
    ):
        facts.add("followup_request")

    if _has_frame(
        frames,
        action="confirm",
        object="quote",
        state="budget_approved",
    ):
        facts.add("budget_approved")

    if _has_frame(
        frames,
        action="report",
        object="procurement",
        state="progressing",
    ):
        facts.add("procurement_progressing")

    if _has_frame(
        frames,
        action="accept",
        object="commercial_terms",
        state="rejected",
    ):
        facts.add("commercial_terms_rejected")

    if _has_frame(
        frames,
        action="confirm",
        object="service",
        state="completed",
    ):
        facts.add("service_completed")

    if _has_frame(
        frames,
        action="request",
        object="handoff",
        state="next_step",
    ):
        facts.add("next_step_requested")

    if any(
        frame.relevance == "different_work_item"
        for frame in frames
    ):
        facts.add("different_work_item")

    return facts


def test_core_facts_are_preserved_across_independent_paraphrases() -> None:
    for family_id, required_facts, texts in CORE_FACTS:
        expected = set(required_facts)

        for variant_index, text in enumerate(
            texts,
            start=0,
        ):
            frames = _frames(text)
            observed = _core_facts(frames)

            assert expected.issubset(observed), (
                f"{family_id} variant {variant_index}: "
                "core factual representation was not preserved\n"
                f"expected={sorted(expected)}\n"
                f"observed={sorted(observed)}\n"
                f"frames={frames}"
            )


def test_core_fact_representation_does_not_encode_business_decisions() -> None:
    forbidden = {
        "followup_gap",
        "customer_delay",
        "internal_activity_gap",
        "no_finding",
        "recommendation",
        "support_level",
        "interpretation_class",
    }

    for _family_id, _required, texts in CORE_FACTS:
        for text in texts:
            frames = _frames(text)

            for frame in frames:
                payload = {
                    frame.actor,
                    frame.action,
                    frame.object,
                    frame.state,
                    frame.polarity,
                    frame.temporal_reference,
                    frame.relevance,
                }

                assert forbidden.isdisjoint(
                    payload
                )


def test_core_fact_inventory_is_stable() -> None:
    observed_families = {
        family_id
        for family_id, _required, _texts
        in CORE_FACTS
    }

    assert observed_families == {
        "R1-relevant",
        "R2-supporting",
        "R3-contradictory",
        "R4-irrelevant",
        "R5-service-next-step",
    }