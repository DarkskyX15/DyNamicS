from __future__ import annotations

from datetime import datetime

from ..models import User
from ..utils import from_iso, utcnow
from .base import RepoBase


class UserRepo(RepoBase):
    def create_user(self, username: str, password_hash: str, role: str = "user", status: str = "active") -> User:
        now = utcnow().isoformat()
        cursor = self.execute(
            """
            INSERT INTO users (username, password_hash, role, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (username, password_hash, role, status, now, now),
        )
        return self.get_by_id(cursor.lastrowid)

    def get_by_username(self, username: str) -> User | None:
        row = self.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return self._row_to_user(row) if row else None

    def get_by_id(self, user_id: int) -> User | None:
        row = self.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self._row_to_user(row) if row else None

    def list_all(self) -> list[User]:
        rows = self.execute("SELECT * FROM users ORDER BY id").fetchall()
        return [self._row_to_user(row) for row in rows]

    def update_status(self, user_id: int, status: str) -> None:
        self.execute(
            "UPDATE users SET status = ?, updated_at = ? WHERE id = ?",
            (status, utcnow().isoformat(), user_id),
        )

    @staticmethod
    def _row_to_user(row) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            role=row["role"],
            status=row["status"],
            created_at=from_iso(row["created_at"]),
            updated_at=from_iso(row["updated_at"]),
        )
