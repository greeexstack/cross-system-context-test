from __future__ import annotations

import json

from test_independent_replication_schema import (
    IndependentReplicationCase,
    validate_suite,
)


def load_suite(path: str) -> tuple[IndependentReplicationCase, ...]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, list):
        raise ValueError("fixture root must be a JSON array")

    cases: list[IndependentReplicationCase] = []

    for raw in payload:
        if not isinstance(raw, dict):
            raise ValueError("each fixture case must be an object")

        expected_fields = tuple(
            (field, value)
            for field, value in raw["expected_fields"]
        )

        cases.append(
            IndependentReplicationCase(
                case_id=raw["case_id"],
                primary_interpretation=raw["primary_interpretation"],
                primary_decision_strength=raw["primary_decision_strength"],
                texts=tuple(raw["texts"]),
                expected_fields=expected_fields,
            )
        )

    suite = tuple(cases)
    validate_suite(suite)
    return suite


def test_loader_accepts_generic_external_fixture(tmp_path) -> None:
    fixture = [
        {
            "case_id": "external-example",
            "primary_interpretation": "opaque_primary_label",
            "primary_decision_strength": "moderate",
            "texts": ["text one", "text two"],
            "expected_fields": [
                ["requests_followup", None],
            ],
        }
    ]

    path = tmp_path / "fixture.json"
    path.write_text(
        json.dumps(fixture),
        encoding="utf-8",
    )

    loaded = load_suite(str(path))

    assert len(loaded) == 1
    assert loaded[0].case_id == "external-example"
    assert loaded[0].texts == ("text one", "text two")
    assert loaded[0].expected_fields == (
        ("requests_followup", None),
    )


def test_loader_rejects_non_array_root(tmp_path) -> None:
    path = tmp_path / "fixture.json"
    path.write_text(
        json.dumps({"case_id": "not-a-suite"}),
        encoding="utf-8",
    )

    try:
        load_suite(str(path))
    except ValueError as exc:
        assert "JSON array" in str(exc)
        return

    raise AssertionError("non-array fixture root was accepted")