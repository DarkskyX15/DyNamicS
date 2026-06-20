from __future__ import annotations

import json
import secrets
from urllib.parse import urlunparse

from fastapi import HTTPException

from ..config import settings
from ..models import Slug, Target, User
from ..repos import SlugRepo, TargetRepo, UpdateLogRepo, UpdateTokenRepo
from ..schemas import SlugCreate, SlugUpdate, TargetCreate, TargetUpdate, UpdateTargetRequest
from ..utils import ensure_path, update_token_hash, utcnow


class TargetService:
    def __init__(
        self,
        slug_repo: SlugRepo,
        target_repo: TargetRepo,
        update_token_repo: UpdateTokenRepo,
        update_log_repo: UpdateLogRepo,
    ) -> None:
        self.slug_repo = slug_repo
        self.target_repo = target_repo
        self.update_token_repo = update_token_repo
        self.update_log_repo = update_log_repo

    def _validate_target_data(self, data: dict, existing: Target | None = None) -> dict:
        mode = data.get("mode") or (existing.mode if existing else None)
        if mode not in {"static", "dynamic_ip", "dynamic_url"}:
            raise HTTPException(status_code=422, detail="不支持的 target 模式")
        if mode in {"static", "dynamic_ip"}:
            scheme = data.get("scheme") or (existing.scheme if existing else None)
            host = data.get("host") if "host" in data else (existing.host if existing else None)
            if not scheme:
                raise HTTPException(status_code=422, detail="静态与 dynamic_ip 模式必须提供 scheme")
            if mode == "static" and not host:
                raise HTTPException(status_code=422, detail="static 模式必须提供 host")
        if mode == "dynamic_url":
            full_url = data.get("full_url") if "full_url" in data else (existing.full_url if existing else None)
            if not full_url:
                raise HTTPException(status_code=422, detail="dynamic_url 模式必须提供 full_url")
        return data

    def resolve_target_url(self, target: Target) -> str | None:
        if not target.enabled:
            return None
        if target.mode == "dynamic_url":
            return target.full_url
        if not target.scheme or not target.host:
            return None
        netloc = target.host
        if target.port:
            netloc = f"{netloc}:{target.port}"
        query = ""
        if target.default_query:
            query = "&".join(
                f"{key}={value}"
                for key, value in json.loads(target.default_query).items()
            )
        return urlunparse((target.scheme, netloc, ensure_path(target.base_path), "", query, ""))

    def list_targets(self, user: User) -> list[Target]:
        return self.target_repo.list_all() if user.role == "admin" else self.target_repo.list_by_owner(user.id)

    def get_target(self, user: User, target_id: int) -> Target:
        target = self.target_repo.get_by_id(target_id)
        if target is None:
            raise HTTPException(status_code=404, detail="target 不存在")
        if user.role != "admin" and target.owner_user_id != user.id:
            raise HTTPException(status_code=403, detail="无权访问该 target")
        return target

    def create_target(self, user: User, payload: TargetCreate) -> Target:
        data = self._validate_target_data(payload.model_dump())
        data["last_updated_by_type"] = "ui"
        return self.target_repo.create(user.id, data)

    def update_target(self, user: User, target_id: int, payload: TargetUpdate) -> Target:
        target = self.get_target(user, target_id)
        data = {key: value for key, value in payload.model_dump().items() if value is not None}
        validated = self._validate_target_data(data, target)
        validated["last_updated_by_type"] = "ui"
        updated = self.target_repo.update(target_id, validated)
        if updated is None:
            raise HTTPException(status_code=404, detail="target 不存在")
        return updated

    def delete_target(self, user: User, target_id: int) -> None:
        self.get_target(user, target_id)
        self.target_repo.delete(target_id)

    def list_slugs(self, user: User) -> list[Slug]:
        return self.slug_repo.list_all() if user.role == "admin" else self.slug_repo.list_by_owner(user.id)

    def get_slug(self, user: User, slug_id: int) -> Slug:
        slug = self.slug_repo.get_by_id(slug_id)
        if slug is None:
            raise HTTPException(status_code=404, detail="slug 不存在")
        if user.role != "admin" and slug.owner_user_id != user.id:
            raise HTTPException(status_code=403, detail="无权访问该 slug")
        return slug

    def create_slug(self, user: User, payload: SlugCreate) -> Slug:
        if payload.redirect_code not in settings.allowed_redirect_codes:
            raise HTTPException(status_code=422, detail="不支持的跳转状态码")
        if self.slug_repo.get_by_slug(payload.slug):
            raise HTTPException(status_code=409, detail="slug 已存在")
        return self.slug_repo.create(user.id, payload.model_dump())

    def update_slug(self, user: User, slug_id: int, payload: SlugUpdate) -> Slug:
        slug = self.get_slug(user, slug_id)
        data = {key: value for key, value in payload.model_dump().items() if value is not None}
        if "redirect_code" in data and data["redirect_code"] not in settings.allowed_redirect_codes:
            raise HTTPException(status_code=422, detail="不支持的跳转状态码")
        if "slug" in data:
            existing = self.slug_repo.get_by_slug(data["slug"])
            if existing and existing.id != slug_id:
                raise HTTPException(status_code=409, detail="slug 已存在")
        if "target_id" in data:
            self.get_target(user, data["target_id"])
        updated = self.slug_repo.update(slug_id, data)
        if updated is None:
            raise HTTPException(status_code=404, detail="slug 不存在")
        return updated

    def delete_slug(self, user: User, slug_id: int) -> None:
        self.get_slug(user, slug_id)
        self.slug_repo.delete(slug_id)

    def create_update_token(self, user: User, target_id: int, label: str, expires_at) -> tuple[str, object]:
        self.get_target(user, target_id)
        plain_token = secrets.token_urlsafe(24)
        stored = self.update_token_repo.create(target_id, label, update_token_hash(plain_token), expires_at)
        return plain_token, stored

    def set_update_token_enabled(self, user: User, token_id: int, enabled: bool) -> None:
        token = self.update_token_repo.get_by_id(token_id)
        if token is None:
            raise HTTPException(status_code=404, detail="更新令牌不存在")
        self.get_target(user, token.target_id)
        self.update_token_repo.set_enabled(token_id, enabled)

    def delete_update_token(self, user: User, token_id: int) -> None:
        token = self.update_token_repo.get_by_id(token_id)
        if token is None:
            raise HTTPException(status_code=404, detail="更新令牌不存在")
        self.get_target(user, token.target_id)
        self.update_token_repo.delete(token_id)

    def list_update_tokens(self, user: User, target_id: int):
        self.get_target(user, target_id)
        return self.update_token_repo.list_by_target(target_id)

    def list_update_logs(self, user: User, target_id: int):
        self.get_target(user, target_id)
        return self.update_log_repo.list_by_target(target_id)

    def update_target_by_token(self, token_value: str, payload: UpdateTargetRequest) -> Target:
        token = self.update_token_repo.get_by_hash(update_token_hash(token_value))
        if token is None or not token.enabled:
            raise HTTPException(status_code=401, detail="更新令牌无效")
        if token.expires_at and token.expires_at < utcnow():
            raise HTTPException(status_code=401, detail="更新令牌已过期")
        target = self.target_repo.get_by_id(token.target_id)
        if target is None or not target.enabled:
            raise HTTPException(status_code=404, detail="target 不存在或已禁用")
        update_data: dict[str, object] = {"last_updated_by_type": "token_api"}
        old_snapshot = self._target_snapshot(target)
        if target.mode == "dynamic_ip":
            if not payload.host or payload.url:
                raise HTTPException(status_code=422, detail="dynamic_ip 模式仅接受 host")
            update_data["host"] = payload.host
        elif target.mode == "dynamic_url":
            if not payload.url or payload.host:
                raise HTTPException(status_code=422, detail="dynamic_url 模式仅接受 url")
            update_data["full_url"] = payload.url
        else:
            raise HTTPException(status_code=422, detail="static 模式不支持令牌更新")
        updated = self.target_repo.update(target.id, update_data)
        if updated is None:
            raise HTTPException(status_code=404, detail="target 不存在")
        self.update_token_repo.touch_last_used(token.id)
        self.update_log_repo.create(updated.id, "token_api", old_snapshot, self._target_snapshot(updated))
        return updated

    def _target_snapshot(self, target: Target) -> dict[str, object]:
        return {
            "id": target.id,
            "mode": target.mode,
            "scheme": target.scheme,
            "host": target.host,
            "port": target.port,
            "base_path": target.base_path,
            "default_query": json.loads(target.default_query or "{}") if target.default_query else {},
            "full_url": target.full_url,
            "enabled": target.enabled,
            "resolved_url": self.resolve_target_url(target),
        }
