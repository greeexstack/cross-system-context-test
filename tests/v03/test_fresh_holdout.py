from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FreshHoldoutCase:
    family_id: str
    primary_interpretation: str
    primary_decision_strength: str
    texts: tuple[str, ...]
    expected_fields: tuple[tuple[str, bool], ...]


FRESH_HOLDOUT: tuple[FreshHoldoutCase, ...] = (
    FreshHoldoutCase(
        family_id="FH1-followup",
        primary_interpretation="quote_pending_decision",
        primary_decision_strength="moderate",
        texts=(
            "Could you circle back with the revised figures on this proposal once the finance review is finished?",
            "After finance signs off on this proposal, please send the updated numbers back to us.",
            "When the figures for this request have cleared internal review, come back with the revised set.",
            "Once the finance check on this quote is complete, we'd like another pass at the updated numbers.",
        ),
        expected_fields=(
            ("requests_followup", True),
        ),
    ),
    FreshHoldoutCase(
        family_id="FH2-supporting",
        primary_interpretation="quote_pending_decision",
        primary_decision_strength="moderate",
        texts=(
            "The purchasing committee has approved the proposed terms for this request.",
            "Procurement has given its formal sign-off on the proposal under review.",
            "The proposed commercial terms for this quote have received purchasing approval.",
            "The buying team has cleared the submitted terms for this deal.",
        ),
        expected_fields=(
            ("confirms_approval", True),
        ),
    ),
    FreshHoldoutCase(
        family_id="FH3-contradictory",
        primary_interpretation="negotiation_open",
        primary_decision_strength="moderate",
        texts=(
            "Legal will not accept the indemnity wording in this proposal in its current form.",
            "The legal team has rejected the indemnity language in the submitted deal as written.",
            "Counsel has declined the present version of the indemnity clause for this request.",
            "The current indemnity text does not pass legal review for this quote.",
        ),
        expected_fields=(
            ("expresses_rejection", True),
        ),
    ),
    FreshHoldoutCase(
        family_id="FH4-irrelevant",
        primary_interpretation="quote_pending_decision",
        primary_decision_strength="moderate",
        texts=(
            "The manufacturing team opened a separate equipment-upgrade project.",
            "A different initiative has started for replacing the plant machinery.",
            "Operations is pursuing another work item focused on equipment renewal.",
            "The plant is running a separate machinery-modernization effort.",
        ),
        expected_fields=(
            ("concerns_same_work_item", False),
        ),
    ),
    FreshHoldoutCase(
        family_id="FH5-service-next-step",
        primary_interpretation="service_completed_next_step_unrecorded",
        primary_decision_strength="moderate",
        texts=(
            "The migration is complete; please arrange the post-migration review for this rollout.",
            "Deployment has finished, and the team should schedule the handoff session for this service transition.",
            "The rollout is now done, so set up the final validation meeting for this release.",
            "The service transition has been completed; the next action is to book the closure review for this engagement.",
        ),
        expected_fields=(
            ("confirms_completion", True),
            ("requests_next_step", True),
        ),
    ),
)


def test_fresh_holdout_shape() -> None:
    assert len(FRESH_HOLDOUT) == 5
    assert all(len(case.texts) == 4 for case in FRESH_HOLDOUT)
    assert {
        case.family_id for case in FRESH_HOLDOUT
    } == {
        "FH1-followup",
        "FH2-supporting",
        "FH3-contradictory",
        "FH4-irrelevant",
        "FH5-service-next-step",
    }


def test_fresh_holdout_oracle_is_fixed() -> None:
    expected = {
        "FH1-followup": (("requests_followup", True),),
        "FH2-supporting": (("confirms_approval", True),),
        "FH3-contradictory": (("expresses_rejection", True),),
        "FH4-irrelevant": (("concerns_same_work_item", False),),
        "FH5-service-next-step": (
            ("confirms_completion", True),
            ("requests_next_step", True),
        ),
    }

    observed = {
        case.family_id: case.expected_fields
        for case in FRESH_HOLDOUT
    }

    assert observed == expected