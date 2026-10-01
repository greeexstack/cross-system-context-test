from __future__ import annotations

from pathlib import Path

from experiment.v03.event_frame_adapter import frames_to_semantics
from experiment.v03.clause_local_extractor_v2 import (
    ClauseLocalRelationalEventFrameExtractor,
)
from test_independent_replication_loader import load_suite


FIXTURE = (
    Path(__file__).parent
    / "independent_replication"
    / "fixture.json"
)


def _expected_transition_activation(case) -> bool:
    fields = dict(case.expected_fields)

    if fields.get("requests_followup") is True:
        return True

    if fields.get("expresses_acceptance") is True:
        return True

    if fields.get("expresses_rejection") is True:
        return True

    if fields.get("confirms_approval") is True:
        return True

    if (
        fields.get("confirms_completion") is True
        and fields.get("requests_next_step") is True
    ):
        return True

    return False


def _candidate_transition_activation(semantics) -> bool:
    if semantics.requests_followup is True:
        return True

    if semantics.expresses_acceptance is True:
        return True

    if semantics.expresses_rejection is True:
        return True

    if semantics.confirms_approval is True:
        return True

    if (
        semantics.confirms_completion is True
        and semantics.requests_next_step is True
    ):
        return True

    return False


def test_independent_semantic_activation() -> None:
    cases = load_suite(str(FIXTURE))
    extractor = ClauseLocalRelationalEventFrameExtractor()

    expected_active = 0
    candidate_active = 0
    false_activations = 0

    for case in cases:
        for variant_index, text in enumerate(case.texts, start=1):
            expected = _expected_transition_activation(case)

            frames = extractor.extract(content=text).frames
            semantics = frames_to_semantics(frames)

            observed = _candidate_transition_activation(semantics)

            if expected:
                expected_active += 1

            if observed:
                candidate_active += 1

            if observed and not expected:
                false_activations += 1

            print(
                case.case_id,
                f"variant={variant_index}",
                f"expected_active={expected}",
                f"candidate_active={observed}",
                f"semantics={semantics}",
            )

    print("\n=== SEMANTIC ACTIVATION SUMMARY ===")
    print(f"expected transition-active variants: {expected_active}/20")
    print(f"candidate transition-active variants: {candidate_active}/20")
    print(f"false activations: {false_activations}/20")