from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ["CROSS_SYSTEM_USER_STORAGE_PATH"] = ":memory:"

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

def test_create_integrated_evaluation() -> None:
    payload = {
        "name": "CRM Integration Test",
        "objective": (
            "Evaluate whether customer communication changes "
            "the opportunity interpretation."
        ),
        "primary": {
            "record_id": "opp_001",
            "record_type": "opportunity",
            "summary": (
                "A quote was sent to the customer and no decision "
                "has been recorded."
            ),
            "customer": {
                "id": "crm_cust_001",
                "name": "Aarav Mehta",
                "email": "aarav@example.com",
                "phone": "+91-9000000001",
            },
            "stage": "quote_sent",
            "value": 85000,
            "quote_sent_at": "2026-09-10T09:00:00",
            "last_crm_activity_at": "2026-09-11T10:00:00",
        },
        "secondary": {
            "source_status": "available",
            "communications": [
                {
                    "communication_id": "comm_001",
                    "customer": {
                        "id": "crm_cust_001",
                        "name": "Aarav Mehta",
                        "email": "aarav@example.com",
                        "phone": "+91-9000000001",
                    },
                    "direction": "inbound",
                    "occurred_at": "2026-09-11T14:30:00",
                    "channel": "whatsapp",
                    "topic": "quote",
                    "content": (
    "Customer asked to schedule a review call "
    "about the proposal next week."
),
                }
            ],
        },
        "evaluation_at": "2026-09-12T09:00:00",
    }

    response = client.post(
        "/v1/integrated-evaluations",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["evaluation_version"] == "v0.2-integrated"
    assert body["source"] == "integrated-input"
    assert body["status"] == "completed"

    assert body["name"] == payload["name"]
    assert body["objective"] == payload["objective"]

    assert body["base"]["interpretation_class"] == "quote_pending_decision"
    assert body["variant"]["interpretation_class"] == "quote_followup_pending"

    assert body["interpretation_changed"] is True
    assert body["variant"]["identity_match"] == "confident_match"
    assert body["variant"]["evidence_ids"] == ["comm_001"]

    assert body["assumptions"]
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
def test_list_user_evaluations() -> None:
    payload = {
        "name": "Report Listing Test",
        "objective": (
            "Verify that a completed evaluation appears in the reports list."
        ),
        "workflow": "Sales",
        "record_type": "opportunity",
        "primary_context": (
            "A quote was sent to the customer and no decision "
            "has been recorded yet."
        ),
        "additional_context": (
            "The customer asked for an update and said they are ready "
            "to discuss the next step."
        ),
    }

    create_response = client.post(
        "/v1/user-evaluations",
        json=payload,
    )

    assert create_response.status_code == 200

    run_id = create_response.json()["run_id"]

    list_response = client.get("/v1/user-evaluations")

    assert list_response.status_code == 200

    body = list_response.json()

    assert any(item["run_id"] == run_id for item in body)


def test_list_user_evaluations() -> None:
    payload = {
        "name": "Report Listing Test",
        "objective": (
            "Verify that a completed evaluation appears in the reports list."
        ),
        "workflow": "Sales",
        "record_type": "opportunity",
        "primary_context": (
            "A quote was sent to the customer and no decision "
            "has been recorded yet."
        ),
        "additional_context": (
            "The customer asked for an update and said they are ready "
            "to discuss the next step."
        ),
    }

    create_response = client.post(
        "/v1/user-evaluations",
        json=payload,
    )

    assert create_response.status_code == 200

    run_id = create_response.json()["run_id"]

    list_response = client.get("/v1/user-evaluations")

    assert list_response.status_code == 200

    body = list_response.json()

    assert any(item["run_id"] == run_id for item in body)
def test_delete_user_evaluation() -> None:
    payload = {
        "name": "API Delete Test",
        "objective": "Verify that deleting an evaluation removes it from active API reads.",
        "workflow": "Sales",
        "record_type": "opportunity",
        "primary_context": "A quote was sent and no decision has been recorded.",
        "additional_context": "The customer asked for an update.",
    }

    create_response = client.post(
        "/v1/user-evaluations",
        json=payload,
    )

    assert create_response.status_code == 200
    run_id = create_response.json()["run_id"]

    delete_response = client.delete(
        f"/v1/user-evaluations/{run_id}"
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/v1/user-evaluations/{run_id}"
    )

    assert get_response.status_code == 404
    assert get_response.json() == {
        "detail": "User evaluation not found."
    }

    list_response = client.get("/v1/user-evaluations")

    assert list_response.status_code == 200
    assert all(
        item["run_id"] != run_id
        for item in list_response.json()
    )
def test_star_and_unstar_user_evaluation() -> None:
    payload = {
        "name": "API Star Test",
        "objective": "Verify starring and unstarring an evaluation through the API.",
        "workflow": "Sales",
        "record_type": "opportunity",
        "primary_context": "A quote was sent and no decision has been recorded.",
        "additional_context": "The customer asked for an update.",
    }

    create_response = client.post(
        "/v1/user-evaluations",
        json=payload,
    )

    assert create_response.status_code == 200
    run_id = create_response.json()["run_id"]

    star_response = client.post(
        f"/v1/user-evaluations/{run_id}/star"
    )

    assert star_response.status_code == 200
    assert star_response.json()["starred"] is True

    get_starred_response = client.get(
        f"/v1/user-evaluations/{run_id}"
    )

    assert get_starred_response.status_code == 200
    assert get_starred_response.json()["starred"] is True

    unstar_response = client.delete(
        f"/v1/user-evaluations/{run_id}/star"
    )

    assert unstar_response.status_code == 200
    assert unstar_response.json()["starred"] is False

    get_unstarred_response = client.get(
        f"/v1/user-evaluations/{run_id}"
    )

    assert get_unstarred_response.status_code == 200
    assert get_unstarred_response.json()["starred"] is False