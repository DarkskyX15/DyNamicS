from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import settings


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    ensure_parent_dir(settings.database_path)
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def connection_scope() -> Iterator[sqlite3.Connection]:
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    mode TEXT NOT NULL,
    scheme TEXT,
    host TEXT,
    port INTEGER,
    base_path TEXT,
    default_query TEXT,
    full_url TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_updated_by_type TEXT NOT NULL DEFAULT 'ui',
    FOREIGN KEY(owner_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_targets_owner ON targets(owner_user_id);

CREATE TABLE IF NOT EXISTS slugs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    owner_user_id INTEGER NOT NULL,
    target_id INTEGER NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    info_public_enabled INTEGER NOT NULL DEFAULT 1,
    redirect_code INTEGER NOT NULL DEFAULT 302,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(target_id) REFERENCES targets(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_slugs_owner ON slugs(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_slugs_target ON slugs(target_id);

CREATE TABLE IF NOT EXISTS target_update_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    enabled INTEGER NOT NULL DEFAULT 1,
    expires_at TEXT,
    last_used_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(target_id) REFERENCES targets(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_target_update_tokens_target ON target_update_tokens(target_id);

CREATE TABLE IF NOT EXISTS update_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    old_snapshot TEXT NOT NULL,
    new_snapshot TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(target_id) REFERENCES targets(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_update_logs_target_created_at ON update_logs(target_id, created_at DESC);

CREATE TABLE IF NOT EXISTS refresh_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    refresh_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_refresh_sessions_user ON refresh_sessions(user_id);
"""


def init_db() -> None:
    with connection_scope() as connection:
        connection.executescript(SCHEMA_SQL)
