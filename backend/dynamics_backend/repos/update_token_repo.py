from __future__ import annotations

from datetime import datetime

from ..models import UpdateToken
from ..utils import from_iso, utcnow
from .base import RepoBase


class UpdateTokenRepo(RepoBase):
    def create(self, target_id: int, label: str, token_hash: str, expires_at: datetime | None) -> UpdateToken:
        cursor = self.execute(
            """
            INSERT INTO target_update_tokens (target_id, label, token_hash, enabled, expires_at, last_used_at, created_at)
            VALUES (?, ?, ?, 1, ?, NULL, ?)
            """,
            (target_id, label, token_hash, expires_at.isoformat() if expires_at else None, utcnow().isoformat()),
        )
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, token_id: int) -> UpdateToken | None:
        row = self.execute("SELECT * FROM target_update_tokens WHERE id = ?", (token_id,)).fetchone()
        return self._row_to_token(row) if row else None

    def get_by_hash(self, token_hash: str) -> UpdateToken | None:
        row = self.execute("SELECT * FROM target_update_tokens WHERE token_hash = ?", (token_hash,)).fetchone()
        return self._row_to_token(row) if row else None

    def list_by_target(self, target_id: int) -> list[UpdateToken]:
        rows = self.execute("SELECT * FROM target_update_tokens WHERE target_id = ? ORDER BY created_at DESC", (target_id,)).fetchall()
        return [self._row_to_token(row) for row in rows]

    def set_enabled(self, token_id: int, enabled: bool) -> None:
        self.execute("UPDATE target_update_tokens SET enabled = ? WHERE id = ?", (1 if enabled else 0, token_id))

    def delete(self, token_id: int) -> None:
        self.execute("DELETE FROM target_update_tokens WHERE id = ?", (token_id,))

    def touch_last_used(self, token_id: int) -> None:
        self.execute("UPDATE target_update_tokens SET last_used_at = ? WHERE id = ?", (utcnow().isoformat(), token_id))

    @staticmethod
    def _row_to_token(row) -> UpdateToken:
        return UpdateToken(
            id=row["id"],
            target_id=row["target_id"],
            label=row["label"],
            token_hash=row["token_hash"],
            enabled=bool(row["enabled"]),
            expires_at=from_iso(row["expires_at"]),
            last_used_at=from_iso(row["last_used_at"]),
            created_at=from_iso(row["created_at"]),
        )
