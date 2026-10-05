from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import UserEvaluationResult

RETENTION_DAYS = 90


class D1UserEvaluationStore:
    """Cloudflare D1 persistence for product-facing user evaluations."""

    def __init__(self, database) -> None:
        self.database = database

    async def _purge_expired(self) -> None:
        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
        ).isoformat()

        await self.database.prepare(
            """
            DELETE FROM user_evaluations
            WHERE deleted_at IS NOT NULL
              AND starred = 0
              AND deleted_at <= ?
            """
        ).bind(cutoff).run()

    async def save(self, result: UserEvaluationResult) -> None:
        await self.database.prepare(
            """
            INSERT OR REPLACE INTO user_evaluations (
                run_id,
                created_at,
                payload,
                starred,
                deleted_at
            )
            VALUES (?, ?, ?, ?, ?)
            """
        ).bind(
            result.run_id,
            result.created_at.isoformat(),
            result.model_dump_json(),
            int(result.starred),
            (
                result.deleted_at.isoformat()
                if result.deleted_at is not None
                else None
            ),
        ).run()

    async def get(self, run_id: str) -> UserEvaluationResult | None:
        await self._purge_expired()

        row = await self.database.prepare(
            """
            SELECT payload
            FROM user_evaluations
            WHERE run_id = ?
              AND deleted_at IS NULL
            """
        ).bind(run_id).first()

        if row is None:
            return None

        return UserEvaluationResult.model_validate_json(row["payload"])

    async def list_all(self) -> list[UserEvaluationResult]:
        await self._purge_expired()

        result = await self.database.prepare(
            """
            SELECT payload
            FROM user_evaluations
            WHERE deleted_at IS NULL
            ORDER BY starred DESC, created_at DESC, run_id DESC
            """
        ).all()

        return [
            UserEvaluationResult.model_validate_json(row["payload"])
            for row in result["results"]
        ]

    async def delete(self, run_id: str) -> bool:
        await self._purge_expired()

        row = await self.database.prepare(
            """
            SELECT payload
            FROM user_evaluations
            WHERE run_id = ?
              AND deleted_at IS NULL
            """
        ).bind(run_id).first()

        if row is None:
            return False

        result = UserEvaluationResult.model_validate_json(row["payload"])
        result.deleted_at = datetime.now(timezone.utc)

        await self.database.prepare(
            """
            UPDATE user_evaluations
            SET payload = ?, deleted_at = ?
            WHERE run_id = ?
            """
        ).bind(
            result.model_dump_json(),
            result.deleted_at.isoformat(),
            run_id,
        ).run()

        return True

    async def set_starred(
        self,
        run_id: str,
        starred: bool,
    ) -> UserEvaluationResult | None:
        await self._purge_expired()

        row = await self.database.prepare(
            """
            SELECT payload
            FROM user_evaluations
            WHERE run_id = ?
            """
        ).bind(run_id).first()

        if row is None:
            return None

        result = UserEvaluationResult.model_validate_json(row["payload"])
        result.starred = starred

        await self.database.prepare(
            """
            UPDATE user_evaluations
            SET payload = ?, starred = ?
            WHERE run_id = ?
            """
        ).bind(
            result.model_dump_json(),
            int(starred),
            run_id,
        ).run()

        return result
