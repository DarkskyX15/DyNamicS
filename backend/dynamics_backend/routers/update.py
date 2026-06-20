from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_target_service
from ..schemas import TargetResponse, UpdateTargetRequest
from ..services import TargetService

router = APIRouter(prefix="/api/update", tags=["update"])


@router.post("/by-token/{token_value}", response_model=TargetResponse)
def update_target(token_value: str, payload: UpdateTargetRequest, target_service: TargetService = Depends(get_target_service)):
    updated = target_service.update_target_by_token(token_value, payload)
    return TargetResponse(
        id=updated.id,
        owner_user_id=updated.owner_user_id,
        name=updated.name,
        mode=updated.mode,
        scheme=updated.scheme,
        host=updated.host,
        port=updated.port,
        base_path=updated.base_path,
        default_query={}
        if not updated.default_query
        else __import__("json").loads(updated.default_query),
        full_url=updated.full_url,
        enabled=updated.enabled,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
        last_updated_by_type=updated.last_updated_by_type,
        resolved_url=target_service.resolve_target_url(updated),
        slug_count=target_service.target_repo.count_slugs(updated.id),
    )
