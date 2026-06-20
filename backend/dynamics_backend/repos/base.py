from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from ..utils import from_iso, to_iso


def as_bool(value: Any) -> bool:
    return bool(value)


def as_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return from_iso(str(value))


def dumps(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def loads(value: str) -> dict[str, Any]:
    return json.loads(value)


class RepoBase:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        return self.connection.execute(sql, params)

    def executemany(self, sql: str, params: list[tuple[Any, ...]]) -> sqlite3.Cursor:
        return self.connection.executemany(sql, params)

    @staticmethod
    def iso(value: datetime | None) -> str | None:
        return to_iso(value)
