from __future__ import annotations

import json
from typing import Any

from ..models import Target
from ..utils import ensure_path, from_iso, utcnow
from .base import RepoBase


class TargetRepo(RepoBase):
    def create(self, owner_user_id: int, data: dict[str, Any]) -> Target:
        now = utcnow().isoformat()
        cursor = self.execute(
            """
            INSERT INTO targets (
                owner_user_id, name, mode, scheme, host, port, base_path,
                default_query, full_url, enabled, created_at, updated_at, last_updated_by_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                owner_user_id,
                data["name"],
                data["mode"],
                data.get("scheme"),
                data.get("host"),
                data.get("port"),
                ensure_path(data.get("base_path")),
                json.dumps(data.get("default_query", {}), ensure_ascii=False),
                data.get("full_url"),
                1 if data.get("enabled", True) else 0,
                now,
                now,
                data.get("last_updated_by_type", "ui"),
            ),
        )
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, target_id: int) -> Target | None:
        row = self.execute("SELECT * FROM targets WHERE id = ?", (target_id,)).fetchone()
        return self._row_to_target(row) if row else None

    def list_by_owner(self, owner_user_id: int) -> list[Target]:
        rows = self.execute("SELECT * FROM targets WHERE owner_user_id = ? ORDER BY updated_at DESC", (owner_user_id,)).fetchall()
        return [self._row_to_target(row) for row in rows]

    def list_all(self) -> list[Target]:
        rows = self.execute("SELECT * FROM targets ORDER BY updated_at DESC").fetchall()
        return [self._row_to_target(row) for row in rows]

    def update(self, target_id: int, data: dict[str, Any]) -> Target | None:
        existing = self.get_by_id(target_id)
        if existing is None:
            return None
        fields: dict[str, Any] = {
            "name": existing.name,
            "mode": existing.mode,
            "scheme": existing.scheme,
            "host": existing.host,
            "port": existing.port,
            "base_path": existing.base_path,
            "default_query": json.loads(existing.default_query or "{}") if isinstance(existing.default_query, str) else {},
            "full_url": existing.full_url,
            "enabled": existing.enabled,
            "last_updated_by_type": existing.last_updated_by_type,
        }
        fields.update(data)
        self.execute(
            """
            UPDATE targets SET
                name = ?, mode = ?, scheme = ?, host = ?, port = ?, base_path = ?,
                default_query = ?, full_url = ?, enabled = ?, updated_at = ?, last_updated_by_type = ?
            WHERE id = ?
            """,
            (
                fields["name"],
                fields["mode"],
                fields.get("scheme"),
                fields.get("host"),
                fields.get("port"),
                ensure_path(fields.get("base_path")),
                json.dumps(fields.get("default_query", {}), ensure_ascii=False),
                fields.get("full_url"),
                1 if fields.get("enabled", True) else 0,
                utcnow().isoformat(),
                fields.get("last_updated_by_type", existing.last_updated_by_type),
                target_id,
            ),
        )
        return self.get_by_id(target_id)

    def delete(self, target_id: int) -> None:
        self.execute("DELETE FROM targets WHERE id = ?", (target_id,))

    def count_slugs(self, target_id: int) -> int:
        row = self.execute("SELECT COUNT(*) AS count FROM slugs WHERE target_id = ?", (target_id,)).fetchone()
        return int(row["count"])

    @staticmethod
    def _row_to_target(row) -> Target:
        return Target(
            id=row["id"],
            owner_user_id=row["owner_user_id"],
            name=row["name"],
            mode=row["mode"],
            scheme=row["scheme"],
            host=row["host"],
            port=row["port"],
            base_path=row["base_path"],
            default_query=row["default_query"],
            full_url=row["full_url"],
            enabled=bool(row["enabled"]),
            created_at=from_iso(row["created_at"]),
            updated_at=from_iso(row["updated_at"]),
            last_updated_by_type=row["last_updated_by_type"],
        )
