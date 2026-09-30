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
def test_deleted_user_evaluation_is_hidden(tmp_path: Path) -> None:
    from experiment.web.storage import UserEvaluationStore

    database_path = tmp_path / "user_evaluations.sqlite3"

    request = UserEvaluationCreateRequest(
        name="Storage Delete Test",
        objective="Verify that a deleted evaluation is hidden from storage reads.",
        workflow="Sales",
        record_type="opportunity",
        primary_context="A quote was sent and no decision has been recorded.",
        additional_context="The customer asked for an update.",
    )

    service = EvaluationService(
        FIXTURE_ROOT,
        user_storage_path=database_path,
    )
    created = service.run_user_evaluation(request)

    store = UserEvaluationStore(database_path)

    assert store.delete(created.run_id) is True
    assert store.get(created.run_id) is None
    assert all(
        result.run_id != created.run_id
        for result in store.list_all()
    )

def test_starred_user_evaluation_survives_store_reopen(tmp_path: Path) -> None:
    from experiment.web.storage import UserEvaluationStore

    database_path = tmp_path / "user_evaluations.sqlite3"

    request = UserEvaluationCreateRequest(
        name="Storage Star Test",
        objective="Verify that a starred evaluation survives reopening storage.",
        workflow="Sales",
        record_type="opportunity",
        primary_context="A quote was sent and no decision has been recorded.",
        additional_context="The customer asked for an update.",
    )

    service = EvaluationService(
        FIXTURE_ROOT,
        user_storage_path=database_path,
    )
    created = service.run_user_evaluation(request)

    first_store = UserEvaluationStore(database_path)
    starred = first_store.set_starred(created.run_id, True)

    assert starred is not None
    assert starred.starred is True

    second_store = UserEvaluationStore(database_path)
    retrieved = second_store.get(created.run_id)

    assert retrieved is not None
    assert retrieved.starred is True

def test_deleted_unstarred_evaluation_is_purged_after_retention(
    tmp_path: Path,
) -> None:
    import sqlite3
    from datetime import datetime, timedelta, timezone

    from experiment.web.storage import UserEvaluationStore

    database_path = tmp_path / "user_evaluations.sqlite3"

    request = UserEvaluationCreateRequest(
        name="Storage Purge Test",
        objective="Verify that an old deleted evaluation is physically purged.",
        workflow="Sales",
        record_type="opportunity",
        primary_context="A quote was sent and no decision has been recorded.",
        additional_context="The customer asked for an update.",
    )

    service = EvaluationService(
        FIXTURE_ROOT,
        user_storage_path=database_path,
    )
    created = service.run_user_evaluation(request)

    store = UserEvaluationStore(database_path)
    assert store.delete(created.run_id) is True

    expired_at = (
        datetime.now(timezone.utc) - timedelta(days=91)
    ).isoformat()

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE user_evaluations
            SET deleted_at = ?
            WHERE run_id = ?
            """,
            (expired_at, created.run_id),
        )

    store.purge_expired()

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT run_id
            FROM user_evaluations
            WHERE run_id = ?
            """,
            (created.run_id,),
        ).fetchone()

    assert row is None

def test_deleted_starred_evaluation_survives_retention_purge(
    tmp_path: Path,
) -> None:
    import sqlite3
    from datetime import datetime, timedelta, timezone

    from experiment.web.storage import UserEvaluationStore

    database_path = tmp_path / "user_evaluations.sqlite3"

    request = UserEvaluationCreateRequest(
        name="Storage Star Retention Test",
        objective="Verify that a starred deleted evaluation survives retention purge.",
        workflow="Sales",
        record_type="opportunity",
        primary_context="A quote was sent and no decision has been recorded.",
        additional_context="The customer asked for an update.",
    )

    service = EvaluationService(
        FIXTURE_ROOT,
        user_storage_path=database_path,
    )
    created = service.run_user_evaluation(request)

    store = UserEvaluationStore(database_path)

    starred = store.set_starred(created.run_id, True)
    assert starred is not None
    assert starred.starred is True

    assert store.delete(created.run_id) is True

    expired_at = (
        datetime.now(timezone.utc) - timedelta(days=91)
    ).isoformat()

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE user_evaluations
            SET deleted_at = ?
            WHERE run_id = ?
            """,
            (expired_at, created.run_id),
        )

    store.purge_expired()

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT starred, deleted_at
            FROM user_evaluations
            WHERE run_id = ?
            """,
            (created.run_id,),
        ).fetchone()

    assert row is not None
    assert row[0] == 1
    assert row[1] is not None
