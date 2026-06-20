from __future__ import annotations

import json
from typing import Any

from ..models import UpdateLog
from ..utils import from_iso, utcnow
from .base import RepoBase


class UpdateLogRepo(RepoBase):
    def create(self, target_id: int, source_type: str, old_snapshot: dict[str, Any], new_snapshot: dict[str, Any]) -> UpdateLog:
        cursor = self.execute(
            """
            INSERT INTO update_logs (target_id, source_type, old_snapshot, new_snapshot, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                target_id,
                source_type,
                json.dumps(old_snapshot, ensure_ascii=False, sort_keys=True),
                json.dumps(new_snapshot, ensure_ascii=False, sort_keys=True),
                utcnow().isoformat(),
            ),
        )
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, log_id: int) -> UpdateLog | None:
        row = self.execute("SELECT * FROM update_logs WHERE id = ?", (log_id,)).fetchone()
        return self._row_to_log(row) if row else None

    def list_by_target(self, target_id: int) -> list[UpdateLog]:
        rows = self.execute("SELECT * FROM update_logs WHERE target_id = ? ORDER BY created_at DESC", (target_id,)).fetchall()
        return [self._row_to_log(row) for row in rows]

    @staticmethod
    def _row_to_log(row) -> UpdateLog:
        return UpdateLog(
            id=row["id"],
            target_id=row["target_id"],
            source_type=row["source_type"],
            old_snapshot=json.loads(row["old_snapshot"]),
            new_snapshot=json.loads(row["new_snapshot"]),
            created_at=from_iso(row["created_at"]),
        )
