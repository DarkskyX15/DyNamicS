from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import jwt

from .config import settings


def utcnow() -> datetime:
    return datetime.now(UTC)


def to_iso(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


def from_iso(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def password_hash(password: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        settings.password_salt.encode("utf-8"),
        100_000,
    )
    return base64.urlsafe_b64encode(digest).decode("ascii")


def verify_password(password: str, stored_hash: str) -> bool:
    return hmac.compare_digest(password_hash(password), stored_hash)


def create_access_token(user_id: int, username: str, role: str) -> str:
    now = utcnow()
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_exp_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("invalid token type")
    return payload


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def refresh_hash(token: str) -> str:
    return hmac.new(
        settings.refresh_secret.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def generate_update_token() -> str:
    return secrets.token_urlsafe(32)


def update_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def merge_query_strings(base_url: str, request_query: dict[str, str]) -> str:
    parsed = urlparse(base_url)
    merged = dict(parse_qsl(parsed.query, keep_blank_values=True))
    merged.update(request_query)
    return urlunparse(parsed._replace(query=urlencode(merged, doseq=True)))


def ensure_path(path: str | None) -> str:
    if not path:
        return ""
    return path if path.startswith("/") else f"/{path}"


def normalize_json_query(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    value = json.loads(raw)
    return {str(key): str(item) for key, item in value.items()}


def dump_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
