from __future__ import annotations

import json

from fastapi import APIRouter, Depends

from ..dependencies import get_current_user, get_target_service
from ..schemas import (
    DashboardResponse,
    MessageResponse,
    SlugCreate,
    SlugResponse,
    SlugUpdate,
    TargetCreate,
    TargetResponse,
    TargetUpdate,
    UpdateLogResponse,
    UpdateTokenCreate,
    UpdateTokenResponse,
    UpdateTokenToggle,
)
from ..services import TargetService

router = APIRouter(prefix="/api", tags=["management"])


def _target_response(target_service: TargetService, target) -> TargetResponse:
    return TargetResponse(
        id=target.id,
        owner_user_id=target.owner_user_id,
        name=target.name,
        mode=target.mode,
        scheme=target.scheme,
        host=target.host,
        port=target.port,
        base_path=target.base_path,
        default_query={} if not target.default_query else json.loads(target.default_query),
        full_url=target.full_url,
        enabled=target.enabled,
        created_at=target.created_at,
        updated_at=target.updated_at,
        last_updated_by_type=target.last_updated_by_type,
        resolved_url=target_service.resolve_target_url(target),
        slug_count=target_service.target_repo.count_slugs(target.id),
    )


def _slug_response(slug) -> SlugResponse:
    return SlugResponse(
        id=slug.id,
        slug=slug.slug,
        owner_user_id=slug.owner_user_id,
        target_id=slug.target_id,
        enabled=slug.enabled,
        info_public_enabled=slug.info_public_enabled,
        redirect_code=slug.redirect_code,
        description=slug.description,
        created_at=slug.created_at,
        updated_at=slug.updated_at,
    )


def _token_response(token, plain_token: str | None = None) -> UpdateTokenResponse:
    return UpdateTokenResponse(
        id=token.id,
        target_id=token.target_id,
        label=token.label,
        enabled=token.enabled,
        expires_at=token.expires_at,
        last_used_at=token.last_used_at,
        created_at=token.created_at,
        plain_token=plain_token,
    )


def _log_response(log) -> UpdateLogResponse:
    return UpdateLogResponse(
        id=log.id,
        target_id=log.target_id,
        source_type=log.source_type,
        old_snapshot=log.old_snapshot,
        new_snapshot=log.new_snapshot,
        created_at=log.created_at,
    )


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    targets = target_service.list_targets(user)
    slugs = target_service.list_slugs(user)
    token_count = sum(len(target_service.list_update_tokens(user, target.id)) for target in targets)
    latest_targets = [_target_response(target_service, target) for target in targets[:5]]
    return DashboardResponse(
        slug_count=len(slugs),
        target_count=len(targets),
        token_count=token_count,
        latest_targets=latest_targets,
    )


@router.get("/targets", response_model=list[TargetResponse])
def list_targets(user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    return [_target_response(target_service, item) for item in target_service.list_targets(user)]


@router.post("/targets", response_model=TargetResponse)
def create_target(payload: TargetCreate, user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    return _target_response(target_service, target_service.create_target(user, payload))


@router.get("/targets/{target_id}", response_model=TargetResponse)
def get_target(target_id: int, user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    return _target_response(target_service, target_service.get_target(user, target_id))


@router.patch("/targets/{target_id}", response_model=TargetResponse)
def update_target(target_id: int, payload: TargetUpdate, user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    return _target_response(target_service, target_service.update_target(user, target_id, payload))


@router.delete("/targets/{target_id}", response_model=MessageResponse)
def delete_target(target_id: int, user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    target_service.delete_target(user, target_id)
    return MessageResponse(message="target 已删除")


@router.get("/slugs", response_model=list[SlugResponse])
def list_slugs(user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    slugs = target_service.list_slugs(user)
    return [_slug_response(slug) for slug in slugs]


@router.post("/slugs", response_model=SlugResponse)
def create_slug(payload: SlugCreate, user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    return _slug_response(target_service.create_slug(user, payload))


@router.get("/slugs/{slug_id}", response_model=SlugResponse)
def get_slug(slug_id: int, user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    return _slug_response(target_service.get_slug(user, slug_id))


@router.patch("/slugs/{slug_id}", response_model=SlugResponse)
def update_slug(slug_id: int, payload: SlugUpdate, user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    return _slug_response(target_service.update_slug(user, slug_id, payload))


@router.delete("/slugs/{slug_id}", response_model=MessageResponse)
def delete_slug(slug_id: int, user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    target_service.delete_slug(user, slug_id)
    return MessageResponse(message="slug 已删除")


@router.get("/targets/{target_id}/tokens", response_model=list[UpdateTokenResponse])
def list_tokens(target_id: int, user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    tokens = target_service.list_update_tokens(user, target_id)
    return [_token_response(token) for token in tokens]


@router.post("/targets/{target_id}/tokens", response_model=UpdateTokenResponse)
def create_token(target_id: int, payload: UpdateTokenCreate, user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    plain_token, token = target_service.create_update_token(user, target_id, payload.label, payload.expires_at)
    return _token_response(token, plain_token=plain_token)


@router.patch("/tokens/{token_id}", response_model=MessageResponse)
def toggle_token(token_id: int, payload: UpdateTokenToggle, user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    target_service.set_update_token_enabled(user, token_id, payload.enabled)
    return MessageResponse(message="更新令牌状态已更新")


@router.delete("/tokens/{token_id}", response_model=MessageResponse)
def delete_token(token_id: int, user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    target_service.delete_update_token(user, token_id)
    return MessageResponse(message="更新令牌已删除")


@router.get("/targets/{target_id}/logs", response_model=list[UpdateLogResponse])
def list_logs(target_id: int, user=Depends(get_current_user), target_service: TargetService = Depends(get_target_service)):
    logs = target_service.list_update_logs(user, target_id)
    return [_log_response(log) for log in logs]
