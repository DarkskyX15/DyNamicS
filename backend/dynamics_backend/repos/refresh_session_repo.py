from __future__ import annotations

from datetime import datetime

from ..models import RefreshSession
from ..utils import from_iso, utcnow
from .base import RepoBase


class RefreshSessionRepo(RepoBase):
    def create(self, user_id: int, refresh_hash: str, expires_at: datetime) -> RefreshSession:
        cursor = self.execute(
            """
            INSERT INTO refresh_sessions (user_id, refresh_hash, expires_at, revoked_at, created_at)
            VALUES (?, ?, ?, NULL, ?)
            """,
            (user_id, refresh_hash, expires_at.isoformat(), utcnow().isoformat()),
        )
        return self.get_by_id(cursor.lastrowid)

    def get_by_hash(self, refresh_hash: str) -> RefreshSession | None:
        row = self.execute("SELECT * FROM refresh_sessions WHERE refresh_hash = ?", (refresh_hash,)).fetchone()
        return self._row_to_session(row) if row else None

    def get_by_id(self, session_id: int) -> RefreshSession | None:
        row = self.execute("SELECT * FROM refresh_sessions WHERE id = ?", (session_id,)).fetchone()
        return self._row_to_session(row) if row else None

    def revoke(self, session_id: int) -> None:
        self.execute("UPDATE refresh_sessions SET revoked_at = ? WHERE id = ?", (utcnow().isoformat(), session_id))

    def revoke_all_for_user(self, user_id: int) -> None:
        self.execute("UPDATE refresh_sessions SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL", (utcnow().isoformat(), user_id))

    @staticmethod
    def _row_to_session(row) -> RefreshSession:
        return RefreshSession(
            id=row["id"],
            user_id=row["user_id"],
            refresh_hash=row["refresh_hash"],
            expires_at=from_iso(row["expires_at"]),
            revoked_at=from_iso(row["revoked_at"]),
            created_at=from_iso(row["created_at"]),
        )
