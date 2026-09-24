from __future__ import annotations

from fastapi.testclient import TestClient

from experiment.web.app import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_run_frozen_v02_evaluation() -> None:
    response = client.post(
        "/v1/evaluations",
        json={
            "evaluation_version": "v0.2",
            "source": "frozen-fixtures",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["evaluation_version"] == "v0.2"
    assert body["source"] == "frozen-fixtures"
    assert body["total_cases"] == 20
    assert body["passed_cases"] == 20
    assert len(body["cases"]) == 20
    assert set(body["dimensions"]) == {
        "context_sensitivity",
        "context_resistance",
        "direction_correctness",
        "evidence_validity",
        "identity_integrity",
        "temporal_integrity",
        "ambiguity_handling",
        "missing_data_handling",
        "generalization",
    }


def test_get_case_after_evaluation() -> None:
    run = client.post(
        "/v1/evaluations",
        json={
            "evaluation_version": "v0.2",
            "source": "frozen-fixtures",
        },
    )

    run_id = run.json()["run_id"]

    response = client.get(
        f"/v1/evaluations/{run_id}/cases/F01-D1"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["pair_id"] == "F01-D1"
    assert "base" in body
    assert "variant" in body
    assert "dimensions" in body


def test_unsupported_evaluation_version_is_rejected() -> None:
    response = client.post(
        "/v1/evaluations",
        json={
            "evaluation_version": "v999",
            "source": "frozen-fixtures",
        },
    )

    assert response.status_code == 422