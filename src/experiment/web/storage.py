from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import UserEvaluationResult


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
                    payload TEXT NOT NULL
                )
                """
            )

    def save(self, result: UserEvaluationResult) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO user_evaluations (
                    run_id,
                    created_at,
                    payload
                )
                VALUES (?, ?, ?)
                """,
                (
                    result.run_id,
                    result.created_at.isoformat(),
                    result.model_dump_json(),
                ),
            )

    def get(self, run_id: str) -> UserEvaluationResult | None:
        with self._connect() as connection:
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

        return UserEvaluationResult.model_validate_json(
            row["payload"]
        )

    def list_all(self) -> list[UserEvaluationResult]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload
                FROM user_evaluations
                ORDER BY created_at DESC, run_id DESC
                """
            ).fetchall()

        return [
            UserEvaluationResult.model_validate_json(row["payload"])
            for row in rows
        ]