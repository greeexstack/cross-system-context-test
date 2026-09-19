from __future__ import annotations


DISENTANGLEMENT_BATTERY = (
    (
        "F1-budget-only",
        (
            (
                "Finance approved the proposed expenditure.",
                {"budget_approved"},
            ),
            (
                "The requested amount received formal financial clearance.",
                {"budget_approved"},
            ),
            (
                "The spending authorization was granted by the finance team.",
                {"budget_approved"},
            ),
            (
                "The quoted amount has been approved under budget.",
                {"budget_approved"},
            ),
        ),
    ),
    (
        "F2-procurement-only",
        (
            (
                "Procurement has opened the purchasing request.",
                {"procurement_progressing"},
            ),
            (
                "The buying team has started processing the order.",
                {"procurement_progressing"},
            ),
            (
                "Sourcing is now working through the purchase request.",
                {"procurement_progressing"},
            ),
            (
                "The purchasing workflow is moving forward.",
                {"procurement_progressing"},
            ),
        ),
    ),
    (
        "F3-service-completion-only",
        (
            (
                "The implementation workshop has been completed.",
                {"service_completed"},
            ),
            (
                "The deployment session has concluded.",
                {"service_completed"},
            ),
            (
                "The migration work is now finished.",
                {"service_completed"},
            ),
            (
                "The onboarding exercise has wrapped up.",
                {"service_completed"},
            ),
        ),
    ),
    (
        "F4-next-step-only",
        (
            (
                "The customer asked what happens next.",
                {"next_step_requested"},
            ),
            (
                "The client requested guidance on the next stage.",
                {"next_step_requested"},
            ),
            (
                "The buyer wants to know what follows.",
                {"next_step_requested"},
            ),
            (
                "The customer asked about the subsequent handoff.",
                {"next_step_requested"},
            ),
        ),
    ),
    (
        "F5-budget-and-procurement",
        (
            (
                "Finance approved the expenditure, and procurement began its intake.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
            (
                "The proposed spend was cleared while purchasing started the order.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
            (
                "Funding was authorized and the sourcing workflow is underway.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
            (
                "The amount received approval, and the buying process is progressing.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
        ),
    ),
    (
        "F6-service-and-next-step",
        (
            (
                "The implementation finished, and the client asked about the handoff.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
            (
                "The deployment concluded, and the customer wants guidance on what follows.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
            (
                "The migration is complete, and the client asked about the next stage.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
            (
                "The onboarding workshop ended, and the customer requested direction for the subsequent transition.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
        ),
    ),
)


def test_disentanglement_battery_shape() -> None:
    assert len(DISENTANGLEMENT_BATTERY) == 6

    texts = [
        text
        for _family_id, variants in DISENTANGLEMENT_BATTERY
        for text, _facts in variants
    ]

    assert len(texts) == 24
    assert len(set(texts)) == 24

    for family_id, variants in DISENTANGLEMENT_BATTERY:
        assert family_id.startswith("F")
        assert len(variants) == 4
        assert all(text.strip() for text, _facts in variants)
        assert all(facts for _text, facts in variants)