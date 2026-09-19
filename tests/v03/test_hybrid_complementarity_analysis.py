from __future__ import annotations

from experiment.v03.clause_local_extractor_v2 import (
    ClauseLocalRelationalEventFrameExtractor,
)
from experiment.v03.spacy_dependency_extractor import (
    SpacyDependencyEventFrameExtractor,
)

from test_hybrid_complementarity_battery import HYBRID_BATTERY


V2 = "clause_local_v2"
SPACY = "spacy_dependency"


V2_EXTRACTOR = ClauseLocalRelationalEventFrameExtractor()
SPACY_EXTRACTOR = SpacyDependencyEventFrameExtractor()


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

    return facts


def _facts(candidate: str, text: str) -> set[str]:
    if candidate == V2:
        frames = V2_EXTRACTOR.extract(content=text).frames
    elif candidate == SPACY:
        frames = SPACY_EXTRACTOR.extract(content=text).frames
    else:
        raise ValueError(candidate)

    return _core_facts(frames)


def test_hybrid_error_overlap() -> None:
    counts = {
        "both_correct": 0,
        "v2_only_correct": 0,
        "spacy_only_correct": 0,
        "both_wrong": 0,
    }

    cases = []

    for family_id, variants in HYBRID_BATTERY:
        for variant_index, (text, expected_facts) in enumerate(
            variants,
            start=0,
        ):
            v2_observed = _facts(V2, text)
            spacy_observed = _facts(SPACY, text)

            v2_correct = v2_observed == expected_facts
            spacy_correct = spacy_observed == expected_facts

            if v2_correct and spacy_correct:
                category = "both_correct"
            elif v2_correct:
                category = "v2_only_correct"
            elif spacy_correct:
                category = "spacy_only_correct"
            else:
                category = "both_wrong"

            counts[category] += 1

            case = {
                "family": family_id,
                "variant": variant_index,
                "text": text,
                "expected": sorted(expected_facts),
                "v2": sorted(v2_observed),
                "spacy": sorted(spacy_observed),
                "category": category,
            }

            cases.append(case)
            print(case)

    print("\n=== HYBRID ERROR OVERLAP ===")
    print(counts)

    assert sum(counts.values()) == 16

    # Make the overlap explicit enough to support a later hybrid decision.
    assert all(
        key in counts
        for key in (
            "both_correct",
            "v2_only_correct",
            "spacy_only_correct",
            "both_wrong",
        )
    )


def test_hybrid_upper_bound_is_computed() -> None:
    oracle_available = 0
    both_wrong = 0

    for _family_id, variants in HYBRID_BATTERY:
        for text, expected_facts in variants:
            v2 = _facts(V2, text)
            spacy = _facts(SPACY, text)

            v2_correct = v2 == expected_facts
            spacy_correct = spacy == expected_facts

            if v2_correct or spacy_correct:
                oracle_available += 1
            else:
                both_wrong += 1

    print("\n=== HYBRID ORACLE UPPER BOUND ===")
    print(
        {
            "total": 16,
            "cases_recoverable_by_either": oracle_available,
            "both_wrong": both_wrong,
            "upper_bound": oracle_available / 16,
        }
    )

    assert oracle_available + both_wrong == 16


def test_hybrid_family_overlap() -> None:
    print("\n=== HYBRID FAMILY OVERLAP ===")

    for family_id, variants in HYBRID_BATTERY:
        both_correct = 0
        v2_only = 0
        spacy_only = 0
        both_wrong = 0

        for text, expected_facts in variants:
            v2_correct = _facts(V2, text) == expected_facts
            spacy_correct = _facts(SPACY, text) == expected_facts

            if v2_correct and spacy_correct:
                both_correct += 1
            elif v2_correct:
                v2_only += 1
            elif spacy_correct:
                spacy_only += 1
            else:
                both_wrong += 1

        result = {
            "family": family_id,
            "both_correct": both_correct,
            "v2_only_correct": v2_only,
            "spacy_only_correct": spacy_only,
            "both_wrong": both_wrong,
        }

        print(result)

        assert (
            both_correct
            + v2_only
            + spacy_only
            + both_wrong
            == 4
        )