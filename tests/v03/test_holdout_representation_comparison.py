from __future__ import annotations

from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)
from experiment.v03.event_frames import (
    CanonicalEventFrameExtractor,
)

from test_event_frame_holdout import HOLDOUT


def _old_core_facts(text: str) -> set[str]:
    extractor = LexicalNormalizationSemanticExtractor()

    result = extractor.extract(
        evidence_id="OLD-HOLDOUT",
        content=text,
        source_system="holdout",
        record_id="OLD-HOLDOUT",
        occurred_at="2026-09-12T10:00:00+00:00",
        customer_id="HOLDOUT-CUSTOMER",
    )

    semantics = result.evidence.semantics

    facts: set[str] = set()

    if semantics.requests_followup is True:
        facts.add("followup_request")

    if semantics.confirms_approval is True:
        facts.add("budget_approved")

    if (
        "procurement"
        in result.matched_concepts
    ):
        facts.add("procurement_progressing")

    if semantics.expresses_rejection is True:
        facts.add("commercial_terms_rejected")

    if semantics.confirms_completion is True:
        facts.add("service_completed")

    if semantics.requests_next_step is True:
        facts.add("next_step_requested")

    if semantics.concerns_same_work_item is False:
        facts.add("different_work_item")

    return facts


def _candidate_core_facts(text: str) -> set[str]:
    extractor = CanonicalEventFrameExtractor()

    frames = extractor.extract(
        content=text,
    ).frames

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


def test_holdout_core_fact_recall_old_vs_candidate() -> None:
    total = 0
    old_complete = 0
    candidate_complete = 0

    old_partial = 0
    candidate_partial = 0

    old_missed = 0
    candidate_missed = 0

    print(
        "\n=== HOLDOUT CORE-FACT RECALL: OLD VS CANDIDATE ==="
    )

    for family_id, _primary, texts, expected_facts in HOLDOUT:
        for variant_index, text in enumerate(
            texts,
            start=0,
        ):
            total += 1

            old_observed = _old_core_facts(text)
            candidate_observed = _candidate_core_facts(text)

            old_overlap = (
                expected_facts.intersection(
                    old_observed
                )
            )

            candidate_overlap = (
                expected_facts.intersection(
                    candidate_observed
                )
            )

            if expected_facts.issubset(
                old_observed
            ):
                old_complete += 1
            elif old_overlap:
                old_partial += 1
            else:
                old_missed += 1

            if expected_facts.issubset(
                candidate_observed
            ):
                candidate_complete += 1
            elif candidate_overlap:
                candidate_partial += 1
            else:
                candidate_missed += 1

            if (
                old_observed
                != candidate_observed
            ):
                print(
                    {
                        "family": family_id,
                        "variant": variant_index,
                        "expected": sorted(
                            expected_facts
                        ),
                        "old": sorted(
                            old_observed
                        ),
                        "candidate": sorted(
                            candidate_observed
                        ),
                    }
                )

    print(
        {
            "total_variants": total,
            "old_complete": old_complete,
            "old_partial": old_partial,
            "old_missed": old_missed,
            "candidate_complete": candidate_complete,
            "candidate_partial": candidate_partial,
            "candidate_missed": candidate_missed,
            "old_complete_rate": (
                old_complete / total
            ),
            "candidate_complete_rate": (
                candidate_complete / total
            ),
        }
    )

    assert total == 20
    assert (
        old_complete + old_partial + old_missed
        == total
    )
    assert (
        candidate_complete
        + candidate_partial
        + candidate_missed
        == total
    )