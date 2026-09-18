from __future__ import annotations

from experiment.v03.clause_local_extractor import (
    ClauseLocalEventFrameExtractor,
)

from test_clause_local_development_battery import (
    DEVELOPMENT_BATTERY,
)


def _extract(text: str):
    return ClauseLocalEventFrameExtractor().extract(
        content=text,
    )


def _core_facts(frames) -> set[str]:
    facts: set[str] = set()

    for frame in frames:
        if (
            frame.action == "request"
            and frame.object == "followup_conversation"
            and frame.state == "requested"
            and frame.polarity.value == "positive"
        ):
            facts.add("followup_request")

        if (
            frame.action == "confirm"
            and frame.object == "quote"
            and frame.state == "budget_approved"
            and frame.polarity.value == "positive"
        ):
            facts.add("budget_approved")

        if (
            frame.action == "report"
            and frame.object == "procurement"
            and frame.state == "progressing"
            and frame.polarity.value == "positive"
        ):
            facts.add("procurement_progressing")

        if (
            frame.action == "accept"
            and frame.object == "commercial_terms"
            and frame.state == "rejected"
            and frame.polarity.value == "negative"
        ):
            facts.add("commercial_terms_rejected")

        if (
            frame.action == "confirm"
            and frame.object == "service"
            and frame.state == "completed"
            and frame.polarity.value == "positive"
        ):
            facts.add("service_completed")

        if (
            frame.action == "request"
            and frame.object in {"handoff", "next_step"}
            and frame.state == "next_step"
            and frame.polarity.value == "positive"
        ):
            facts.add("next_step_requested")

        if frame.relevance == "different_work_item":
            facts.add("different_work_item")

    return facts


def test_development_failures_are_explicitly_classified() -> None:
    failures: list[dict[str, object]] = []

    for family_id, _primary_state, variants in DEVELOPMENT_BATTERY:
        for variant_index, (text, expected_facts) in enumerate(
            variants,
            start=0,
        ):
            result = _extract(text)
            observed = _core_facts(result.frames)

            missing = expected_facts - observed
            extra = observed - expected_facts

            if missing or extra:
                failures.append(
                    {
                        "family": family_id,
                        "variant": variant_index,
                        "text": text,
                        "clauses": [
                            {
                                "index": clause.index,
                                "text": clause.text,
                            }
                            for clause in _split_for_diagnostic(text)
                        ],
                        "frames": [
                            {
                                "actor": frame.actor,
                                "action": frame.action,
                                "object": frame.object,
                                "state": frame.state,
                                "polarity": frame.polarity.value,
                                "temporal_reference": frame.temporal_reference,
                                "relevance": frame.relevance,
                            }
                            for frame in result.frames
                        ],
                        "expected": sorted(expected_facts),
                        "observed": sorted(observed),
                        "missing": sorted(missing),
                        "extra": sorted(extra),
                    }
                )

    print("\n=== CLAUSE-LOCAL DEVELOPMENT FAILURE ANALYSIS ===")

    for failure in failures:
        print(failure)

    print(
        {
            "failure_count": len(failures),
            "failures": [
                (
                    item["family"],
                    item["variant"],
                    item["missing"],
                )
                for item in failures
            ],
        }
    )

    assert len(failures) == 4


def _split_for_diagnostic(text: str):
    extractor = ClauseLocalEventFrameExtractor()

    normalized = extractor._normalize(text)

    return extractor._split_clauses(normalized)


def test_failure_classes_are_distinct() -> None:
    expected = {
        (
            "D2-supporting",
            2,
            "budget_approved",
        ),
        (
            "D3-contradictory",
            0,
            "commercial_terms_rejected",
        ),
        (
            "D4-irrelevant",
            0,
            "different_work_item",
        ),
        (
            "D5-service-next-step",
            0,
            "next_step_requested",
        ),
    }

    observed = set()

    for family_id, _primary_state, variants in DEVELOPMENT_BATTERY:
        for variant_index, (text, expected_facts) in enumerate(
            variants,
            start=0,
        ):
            result = _extract(text)
            observed_facts = _core_facts(result.frames)
            missing = expected_facts - observed_facts

            for fact in missing:
                observed.add(
                    (
                        family_id,
                        variant_index,
                        fact,
                    )
                )

    assert observed == expected