from __future__ import annotations

import json

from experiment.v03.measure import (
    report_as_dict,
    report_as_json,
    run_v03_measurement,
    write_report,
)


def test_measurement_runs_full_v03_battery():
    report = run_v03_measurement()

    assert report.total_cases == 10
    assert report.directional_correct == 10
    assert report.directional_correctness_rate == 1.0
    assert report.unsupported_change_rate == 0.0

    assert len(report.cases) == 10


def test_measurement_report_contains_all_case_ids():
    report = run_v03_measurement()

    assert {
        case.case_id
        for case in report.cases
    } == {
        "MR1-relevant-followup",
        "MR2-supporting-approval",
        "MR3-contradictory-rejection",
        "MR4-irrelevant-work",
        "MR5-wrong-identity",
        "MR6-ambiguous-identity",
        "MR7-stale",
        "MR8-unavailable-source",
        "MR9-no-secondary",
        "F10-service-next-step",
    }


def test_measurement_report_is_json_serializable():
    payload = report_as_dict()

    encoded = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
    )

    decoded = json.loads(encoded)

    assert decoded["total_cases"] == 10
    assert decoded["directional_correct"] == 10
    assert decoded["directional_correctness_rate"] == 1.0
    assert decoded["unsupported_change_rate"] == 0.0


def test_measurement_report_json_output_is_valid():
    encoded = report_as_json()

    decoded = json.loads(encoded)

    assert decoded["total_cases"] == 10
    assert len(decoded["cases"]) == 10


def test_write_report_creates_reproducible_artifact(tmp_path):
    output_path = tmp_path / "v03_measurement.json"

    written = write_report(output_path)

    assert written == output_path
    assert output_path.exists()

    payload = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    assert payload["total_cases"] == 10
    assert payload["directional_correct"] == 10
    assert payload["directional_correctness_rate"] == 1.0
    assert payload["unsupported_change_rate"] == 0.0