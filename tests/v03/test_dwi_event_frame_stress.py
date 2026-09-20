from __future__ import annotations

import sys
from pathlib import Path


SRC_V03 = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "experiment"
    / "v03"
)

if str(SRC_V03) not in sys.path:
    sys.path.insert(0, str(SRC_V03))


from dwi_event_frame_extractor import extract_event_frame


CASES = [
    (
        "FRAME1",
        "The team is speaking with the buyer about the current quotation.",
        "quotation",
        "CURRENT",
    ),
    (
        "FRAME2",
        "The team is speaking with another buyer about the current quotation.",
        "quotation",
        "CURRENT",
    ),
    (
        "FRAME3",
        "The customer contacted the buyer about the current proposal.",
        "proposal",
        "CURRENT",
    ),
    (
        "FRAME4",
        "The customer contacted another buyer about the current proposal.",
        "proposal",
        "CURRENT",
    ),
    (
        "FRAME5",
        "The team met with procurement after reviewing the current offer.",
        "offer",
        "CURRENT",
    ),
    (
        "FRAME6",
        "The team met with procurement after reviewing a different offer.",
        "offer",
        "DIFFERENT",
    ),
]


def _contains_target(frame, target, status):
    for argument in frame["arguments"]:
        if (
            argument.get("target") == target
            and argument.get("status") == status
        ):
            return True

    for event in frame["subevents"]:
        for argument in event["arguments"]:
            if (
                argument.get("target") == target
                and argument.get("status") == status
            ):
                return True

    return False


def test_event_frame_stress():
    print("\n=== EVENT FRAME STRESS TEST ===")

    correct = 0

    for (
        case_id,
        text,
        expected_target,
        expected_status,
    ) in CASES:
        frame = extract_event_frame(text)

        actual = _contains_target(
            frame,
            expected_target,
            expected_status,
        )

        if actual:
            correct += 1

        print(
            {
                "case": case_id,
                "text": text,
                "frame": frame,
                "expected_target": expected_target,
                "expected_status": expected_status,
                "target_found": actual,
            }
        )

    print("\n=== SUMMARY ===")
    print(
        {
            "correct": correct,
            "total": len(CASES),
            "accuracy": round(
                correct / len(CASES),
                4,
            ),
        }
    )

    assert len(CASES) == 6