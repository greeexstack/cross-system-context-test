from __future__ import annotations

from experiment.v03.event_frames import (
    CanonicalEventFrameExtractor,
)


BATTERY = (
    (
        "R1-relevant",
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


def _fingerprint(text: str) -> tuple:
    extractor = CanonicalEventFrameExtractor()

    result = extractor.extract(
        content=text,
    )

    return tuple(
        (
            frame.actor,
            frame.action,
            frame.object,
            frame.state,
            frame.polarity,
            frame.temporal_reference,
            frame.relevance,
        )
        for frame in result.frames
    )


def test_candidate_extracts_each_independent_variant() -> None:
    extractor = CanonicalEventFrameExtractor()

    for family_id, texts in BATTERY:
        for text in texts:
            result = extractor.extract(
                content=text,
            )

            assert result.frames, (
                f"{family_id}: candidate extractor produced "
                "no factual frames"
            )


def test_candidate_representation_is_stable_across_battery() -> None:
    total_pairs = 0
    stable_pairs = 0
    drift_pairs = 0

    for family_id, texts in BATTERY:
        original = _fingerprint(texts[0])

        for variant_index, text in enumerate(
            texts[1:],
            start=1,
        ):
            total_pairs += 1
            variant = _fingerprint(text)

            if variant == original:
                stable_pairs += 1
            else:
                drift_pairs += 1

                print(
                    f"\nDRIFT {family_id} "
                    f"variant={variant_index}"
                )
                print(f"original={original}")
                print(f"variant={variant}")

    print(
        "\n=== EVENT-FRAME CANDIDATE ==="
    )
    print(
        {
            "total_pairs": total_pairs,
            "stable_pairs": stable_pairs,
            "drift_pairs": drift_pairs,
            "invariance_rate": (
                stable_pairs / total_pairs
            ),
        }
    )

    assert total_pairs == 15
    assert stable_pairs + drift_pairs == total_pairs


def test_candidate_keeps_irrelevance_as_factual_relevance() -> None:
    extractor = CanonicalEventFrameExtractor()

    texts = BATTERY[3][1]

    for text in texts:
        result = extractor.extract(
            content=text,
        )

        assert any(
            frame.relevance == "different_work_item"
            for frame in result.frames
        )