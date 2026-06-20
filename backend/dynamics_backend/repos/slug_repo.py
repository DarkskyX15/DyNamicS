from __future__ import annotations

from typing import Any

from ..models import Slug
from ..utils import from_iso, utcnow
from .base import RepoBase


class SlugRepo(RepoBase):
    def create(self, owner_user_id: int, data: dict[str, Any]) -> Slug:
        now = utcnow().isoformat()
        cursor = self.execute(
            """
            INSERT INTO slugs (slug, owner_user_id, target_id, enabled, info_public_enabled, redirect_code, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["slug"],
                owner_user_id,
                data["target_id"],
                1 if data.get("enabled", True) else 0,
                1 if data.get("info_public_enabled", True) else 0,
                data.get("redirect_code", 302),
                data.get("description", ""),
                now,
                now,
            ),
        )
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, slug_id: int) -> Slug | None:
        row = self.execute("SELECT * FROM slugs WHERE id = ?", (slug_id,)).fetchone()
        return self._row_to_slug(row) if row else None

    def get_by_slug(self, slug: str) -> Slug | None:
        row = self.execute("SELECT * FROM slugs WHERE slug = ?", (slug,)).fetchone()
        return self._row_to_slug(row) if row else None

    def list_by_owner(self, owner_user_id: int) -> list[Slug]:
        rows = self.execute("SELECT * FROM slugs WHERE owner_user_id = ? ORDER BY updated_at DESC", (owner_user_id,)).fetchall()
        return [self._row_to_slug(row) for row in rows]

    def list_all(self) -> list[Slug]:
        rows = self.execute("SELECT * FROM slugs ORDER BY updated_at DESC").fetchall()
        return [self._row_to_slug(row) for row in rows]

    def update(self, slug_id: int, data: dict[str, Any]) -> Slug | None:
        existing = self.get_by_id(slug_id)
        if existing is None:
            return None
        fields = {
            "slug": existing.slug,
            "target_id": existing.target_id,
            "enabled": existing.enabled,
            "info_public_enabled": existing.info_public_enabled,
            "redirect_code": existing.redirect_code,
            "description": existing.description,
        }
        fields.update(data)
        self.execute(
            """
            UPDATE slugs SET slug = ?, target_id = ?, enabled = ?, info_public_enabled = ?, redirect_code = ?, description = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                fields["slug"],
                fields["target_id"],
                1 if fields["enabled"] else 0,
                1 if fields["info_public_enabled"] else 0,
                fields["redirect_code"],
                fields["description"],
                utcnow().isoformat(),
                slug_id,
            ),
        )
        return self.get_by_id(slug_id)

    def delete(self, slug_id: int) -> None:
        self.execute("DELETE FROM slugs WHERE id = ?", (slug_id,))

    @staticmethod
    def _row_to_slug(row) -> Slug:
        return Slug(
            id=row["id"],
            slug=row["slug"],
            owner_user_id=row["owner_user_id"],
            target_id=row["target_id"],
            enabled=bool(row["enabled"]),
            info_public_enabled=bool(row["info_public_enabled"]),
            redirect_code=row["redirect_code"],
            description=row["description"],
            created_at=from_iso(row["created_at"]),
            updated_at=from_iso(row["updated_at"]),
        )
