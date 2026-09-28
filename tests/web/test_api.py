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

def test_create_and_get_user_evaluation() -> None:
    payload = {
        "name": "Quote Follow-up Decision",
        "objective": (
            "Determine whether the latest customer communication "
            "changes the follow-up decision."
        ),
        "workflow": "Sales",
        "record_type": "opportunity",
        "primary_context": (
            "A quote was sent to the customer and no decision "
            "has been recorded yet."
        ),
        "additional_context": (
            "The customer replied asking for an update and said "
            "they are ready to discuss the next step."
        ),
    }

    create_response = client.post(
        "/v1/user-evaluations",
        json=payload,
    )

    assert create_response.status_code == 200

    body = create_response.json()

    assert body["evaluation_version"] == "v0.2-user"
    assert body["source"] == "user-input"
    assert body["status"] == "completed"

    assert body["name"] == payload["name"]
    assert body["objective"] == payload["objective"]
    assert body["workflow"] == payload["workflow"]
    assert body["record_type"] == payload["record_type"]
    assert body["primary_context"] == payload["primary_context"]
    assert body["additional_context"] == payload["additional_context"]

    assert "base" in body
    assert "variant" in body
    assert isinstance(body["interpretation_changed"], bool)
    assert isinstance(body["support_changed"], bool)
    assert isinstance(body["decision_strength_changed"], bool)
    assert body["assumptions"]

    assert body["variant"]["evidence"]
    assert (
        body["variant"]["evidence"][0]["summary"]
        == payload["additional_context"]
    )

    run_id = body["run_id"]

    get_response = client.get(
        f"/v1/user-evaluations/{run_id}"
    )

    assert get_response.status_code == 200

    retrieved = get_response.json()

    assert retrieved["run_id"] == run_id
    assert retrieved["name"] == payload["name"]
    assert retrieved["objective"] == payload["objective"]
    assert retrieved["primary_context"] == payload["primary_context"]
    assert retrieved["additional_context"] == payload["additional_context"]
    assert retrieved["base"] == body["base"]
    assert retrieved["variant"] == body["variant"]

def test_get_missing_user_evaluation() -> None:
    response = client.get(
        "/v1/user-evaluations/nonexistent-run"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "User evaluation not found."
    }
