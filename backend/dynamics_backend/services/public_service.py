from __future__ import annotations

from fastapi import HTTPException

from ..models import Slug, Target
from ..repos import SlugRepo, TargetRepo
from ..schemas import PublicInfoResponse
from ..utils import merge_query_strings
from .target_service import TargetService


class PublicService:
    def __init__(self, slug_repo: SlugRepo, target_repo: TargetRepo, target_service: TargetService) -> None:
        self.slug_repo = slug_repo
        self.target_repo = target_repo
        self.target_service = target_service

    def get_public_slug(self, slug_value: str) -> tuple[Slug, Target]:
        slug = self.slug_repo.get_by_slug(slug_value)
        if slug is None or not slug.enabled:
            raise HTTPException(status_code=404, detail="slug 不存在")
        target = self.target_repo.get_by_id(slug.target_id)
        if target is None or not target.enabled:
            raise HTTPException(status_code=404, detail="target 不存在")
        return slug, target

    def resolve_redirect(self, slug_value: str, query_params: dict[str, str]) -> tuple[int, str]:
        slug, target = self.get_public_slug(slug_value)
        resolved = self.target_service.resolve_target_url(target)
        if not resolved:
            raise HTTPException(status_code=502, detail="目标无法解析")
        return slug.redirect_code, merge_query_strings(resolved, query_params)

    def get_public_info(self, slug_value: str) -> PublicInfoResponse:
        slug, target = self.get_public_slug(slug_value)
        if not slug.info_public_enabled:
            raise HTTPException(status_code=404, detail="slug 信息不可见")
        resolved = self.target_service.resolve_target_url(target)
        if not resolved:
            raise HTTPException(status_code=502, detail="目标无法解析")
        return PublicInfoResponse(
            slug=slug.slug,
            enabled=slug.enabled,
            mode=target.mode,
            target_url=resolved,
            updated_at=target.updated_at,
            description=slug.description,
        )
