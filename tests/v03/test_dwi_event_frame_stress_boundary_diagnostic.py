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
        "FP1",
        "The team is speaking with the buyer about the current quotation.",
        "quotation",
        "CURRENT",
    ),
    (
        "FP2",
        "The team is speaking with another buyer about the current quotation.",
        "quotation",
        "CURRENT",
    ),
    (
        "FP3",
        "The buyer is reviewing the current quotation with the account team.",
        "quotation",
        "CURRENT",
    ),
    (
        "FP4",
        "The buyer is reviewing a separate quotation with the account team.",
        "quotation",
        "DIFFERENT",
    ),
    (
        "FP5",
        "The current quotation was reviewed by the buyer during the meeting.",
        "quotation",
        "CURRENT",
    ),
    (
        "FP6",
        "A separate quotation was reviewed by the buyer during the meeting.",
        "quotation",
        "DIFFERENT",
    ),
    (
        "FP7",
        "The account team is focused on the current agreement with procurement.",
        "agreement",
        "CURRENT",
    ),
    (
        "FP8",
        "The account team is focused on another agreement with procurement.",
        "agreement",
        "DIFFERENT",
    ),
    (
        "FP9",
        "The customer contacted the buyer about the current proposal.",
        "proposal",
        "CURRENT",
    ),
    (
        "FP10",
        "The customer contacted another buyer about the current proposal.",
        "proposal",
        "CURRENT",
    ),
    (
        "FP11",
        "The team met with procurement after reviewing the current offer.",
        "offer",
        "CURRENT",
    ),
    (
        "FP12",
        "The team met with procurement after reviewing a different offer.",
        "offer",
        "DIFFERENT",
    ),
    (
        "FP13",
        "The buyer approved the current quotation.",
        "quotation",
        "CURRENT",
    ),
    (
        "FP14",
        "The buyer rejected a separate quotation.",
        "quotation",
        "DIFFERENT",
    ),
    (
        "FP15",
        "The team is preparing for the meeting with the buyer.",
        None,
        None,
    ),
    (
        "FP16",
        "The account team is working with procurement.",
        None,
        None,
    ),
    (
        "FP17",
        "The buyer discussed the quotation with the team.",
        None,
        None,
    ),
    (
        "FP18",
        "Another buyer contacted the team yesterday.",
        None,
        None,
    ),
    (
        "FP19",
        "The team reviewed the current quotation and another document.",
        "quotation",
        "CURRENT",
    ),
    (
        "FP20",
        "The team reviewed a separate quotation and another document.",
        "quotation",
        "DIFFERENT",
    ),
]


def _all_arguments(frame):
    arguments = list(frame["arguments"])

    for event in frame["subevents"]:
        arguments.extend(event["arguments"])

    return arguments


def _find_target_argument(frame, target):
    for argument in _all_arguments(frame):
        if argument.get("target") == target:
            return argument

    return None


def _has_explicit_status(frame):
    return any(
        argument.get("status") in {
            "CURRENT",
            "DIFFERENT",
        }
        for argument in _all_arguments(frame)
    )


def test_dwi_event_frame_stress_boundary():
    print("\n=== EVENT-FRAME STRESS BOUNDARY ===")

    correct = 0

    for (
        case_id,
        text,
        expected_target,
        expected_status,
    ) in CASES:
        frame = extract_event_frame(text)

        if expected_target is None:
            actual = {
                "neutral": not _has_explicit_status(frame),
            }

            exact = actual["neutral"]

        else:
            target_argument = _find_target_argument(
                frame,
                expected_target,
            )

            exact = (
                target_argument is not None
                and target_argument["status"]
                == expected_status
            )

            actual = {
                "target_argument": target_argument,
            }

        if exact:
            correct += 1

        print(
            {
                "case": case_id,
                "text": text,
                "expected_target": expected_target,
                "expected_status": expected_status,
                "actual": actual,
                "frame": frame,
                "exact": exact,
            }
        )

    print("\n=== SUMMARY ===")
    print(
        {
            "exact": correct,
            "total": len(CASES),
            "accuracy": round(
                correct / len(CASES),
                4,
            ),
        }
    )

    assert len(CASES) == 20