from __future__ import annotations

from pathlib import Path

from experiment.web.models import UserEvaluationCreateRequest
from experiment.web.service import EvaluationService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = PROJECT_ROOT / "fixtures_package"


def test_user_evaluation_survives_store_reopen(tmp_path: Path) -> None:
    database_path = tmp_path / "user_evaluations.sqlite3"

    request = UserEvaluationCreateRequest(
        name="Storage Persistence Test",
        objective="Verify that a completed evaluation survives reopening storage.",
        workflow="Sales",
        record_type="opportunity",
        primary_context=(
            "A quote was sent to the customer and no decision has "
            "been recorded yet."
        ),
        additional_context=(
            "The customer asked for an update and said they are ready "
            "to discuss the next step."
        ),
    )

    first_service = EvaluationService(
        FIXTURE_ROOT,
        user_storage_path=database_path,
    )
    created = first_service.run_user_evaluation(request)

    second_service = EvaluationService(
        FIXTURE_ROOT,
        user_storage_path=database_path,
    )
    retrieved = second_service.get_user(created.run_id)

    assert retrieved is not None
    assert retrieved.run_id == created.run_id
    assert retrieved.name == created.name
    assert retrieved.objective == created.objective
    assert retrieved.primary_context == created.primary_context
    assert retrieved.additional_context == created.additional_context
    assert retrieved.base == created.base
    assert retrieved.variant == created.variant