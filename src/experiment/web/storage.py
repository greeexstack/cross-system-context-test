from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models import UserEvaluationResult


RETENTION_DAYS = 90


class UserEvaluationStore:
    """Durable local storage for product-facing user evaluations."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = database_path
        self._connection: sqlite3.Connection | None = None

        if str(database_path) == ":memory:":
            self._connection = sqlite3.connect(
                ":memory:",
                check_same_thread=False,
            )
            self._connection.row_factory = sqlite3.Row
        else:
            database_path = Path(database_path)
            database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            self.database_path = database_path

        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        if self._connection is not None:
            return self._connection

        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_evaluations (
                    run_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    starred INTEGER NOT NULL DEFAULT 0,
                    deleted_at TEXT
                )
                """
            )

            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(user_evaluations)"
                ).fetchall()
            }

            if "starred" not in columns:
                connection.execute(
                    """
                    ALTER TABLE user_evaluations
                    ADD COLUMN starred INTEGER NOT NULL DEFAULT 0
                    """
                )

            if "deleted_at" not in columns:
                connection.execute(
                    """
                    ALTER TABLE user_evaluations
                    ADD COLUMN deleted_at TEXT
                    """
                )

            self._purge_expired(connection)

    def _purge_expired(
        self,
        connection: sqlite3.Connection,
        now: datetime | None = None,
    ) -> None:
        current_time = now or datetime.now(timezone.utc)
        cutoff = current_time - timedelta(days=RETENTION_DAYS)

        connection.execute(
            """
            DELETE FROM user_evaluations
            WHERE deleted_at IS NOT NULL
              AND starred = 0
              AND deleted_at <= ?
            """,
            (cutoff.isoformat(),),
        )

    def purge_expired(self) -> None:
        with self._connect() as connection:
            self._purge_expired(connection)

    def save(self, result: UserEvaluationResult) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO user_evaluations (
                    run_id,
                    created_at,
                    payload,
                    starred,
                    deleted_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    result.run_id,
                    result.created_at.isoformat(),
                    result.model_dump_json(),
                    int(result.starred),
                    (
                        result.deleted_at.isoformat()
                        if result.deleted_at is not None
                        else None
                    ),
                ),
            )

    def get(self, run_id: str) -> UserEvaluationResult | None:
        with self._connect() as connection:
            self._purge_expired(connection)

            row = connection.execute(
                """
                SELECT payload
                FROM user_evaluations
                WHERE run_id = ?
                  AND deleted_at IS NULL
                """,
                (run_id,),
            ).fetchone()

        if row is None:
            return None

        return UserEvaluationResult.model_validate_json(
            row["payload"]
        )

    def list_all(self) -> list[UserEvaluationResult]:
        with self._connect() as connection:
            self._purge_expired(connection)

            rows = connection.execute(
                """
                SELECT payload
                FROM user_evaluations
                WHERE deleted_at IS NULL
                ORDER BY starred DESC, created_at DESC, run_id DESC
                """
            ).fetchall()

        return [
            UserEvaluationResult.model_validate_json(row["payload"])
            for row in rows
        ]

    def delete(self, run_id: str) -> bool:
        with self._connect() as connection:
            self._purge_expired(connection)

            row = connection.execute(
                """
                SELECT payload
                FROM user_evaluations
                WHERE run_id = ?
                  AND deleted_at IS NULL
                """,
                (run_id,),
            ).fetchone()

            if row is None:
                return False

            result = UserEvaluationResult.model_validate_json(
                row["payload"]
            )

            result.deleted_at = datetime.now(timezone.utc)

            connection.execute(
                """
                UPDATE user_evaluations
                SET payload = ?,
                    deleted_at = ?
                WHERE run_id = ?
                """,
                (
                    result.model_dump_json(),
                    result.deleted_at.isoformat(),
                    run_id,
                ),
            )

            return True

    def set_starred(
        self,
        run_id: str,
        starred: bool,
    ) -> UserEvaluationResult | None:
        with self._connect() as connection:
            self._purge_expired(connection)

            row = connection.execute(
                """
                SELECT payload
                FROM user_evaluations
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()

            if row is None:
                return None

            result = UserEvaluationResult.model_validate_json(
                row["payload"]
            )

            result.starred = starred

            connection.execute(
                """
                UPDATE user_evaluations
                SET payload = ?,
                    starred = ?
                WHERE run_id = ?
                """,
                (
                    result.model_dump_json(),
                    int(starred),
                    run_id,
                ),
            )

            return result