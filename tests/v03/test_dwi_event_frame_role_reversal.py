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


from test_embedding_dwi_role_reversal_battery import CASES
from dwi_event_frame_extractor import extract_event_frame


def _all_arguments(frame):
    arguments = list(frame["arguments"])

    for event in frame["subevents"]:
        arguments.extend(event["arguments"])

    return arguments


def _find_target(frame, target):
    for argument in _all_arguments(frame):
        if argument.get("target") == target:
            return argument

    return None


def test_event_frame_role_reversal():
    print("\n=== EVENT-FRAME ROLE-REVERSAL ===")

    exact = 0

    for (
        pair_id,
        current_text,
        different_text,
    ) in CASES:
        current_frame = extract_event_frame(
            current_text
        )

        different_frame = extract_event_frame(
            different_text
        )

        current_target = _find_target(
            current_frame,
            current_text.split("quotation")[0]
            and None
            or "",
        )

        # Locate the common semantic noun from the pair.
        common_target = next(
            word
            for word in (
                "quotation",
                "proposal",
                "offer",
                "deal",
                "opportunity",
                "agreement",
                "account",
            )
            if word in current_text.lower()
        )

        current_target = _find_target(
            current_frame,
            common_target,
        )

        different_target = _find_target(
            different_frame,
            common_target,
        )

        pair_exact = (
            current_target is not None
            and current_target["status"] == "CURRENT"
            and different_target is not None
            and different_target["status"]
            == "DIFFERENT"
        )

        if pair_exact:
            exact += 1

        print(
            {
                "pair": pair_id,
                "current": current_target,
                "different": different_target,
                "pair_exact": pair_exact,
            }
        )

    print("\n=== SUMMARY ===")
    print(
        {
            "pair_exact": exact,
            "total": len(CASES),
            "accuracy": round(
                exact / len(CASES),
                4,
            ),
        }
    )

    assert len(CASES) == 8