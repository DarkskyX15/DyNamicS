from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class User:
    id: int
    username: str
    password_hash: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class Target:
    id: int
    owner_user_id: int
    name: str
    mode: str
    scheme: str | None
    host: str | None
    port: int | None
    base_path: str | None
    default_query: str | None
    full_url: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime
    last_updated_by_type: str


@dataclass(slots=True)
class Slug:
    id: int
    slug: str
    owner_user_id: int
    target_id: int
    enabled: bool
    info_public_enabled: bool
    redirect_code: int
    description: str
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class UpdateToken:
    id: int
    target_id: int
    label: str
    token_hash: str
    enabled: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime


@dataclass(slots=True)
class UpdateLog:
    id: int
    target_id: int
    source_type: str
    old_snapshot: dict[str, Any]
    new_snapshot: dict[str, Any]
    created_at: datetime


@dataclass(slots=True)
class RefreshSession:
    id: int
    user_id: int
    refresh_hash: str
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime
