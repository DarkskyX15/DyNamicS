from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from ..dependencies import get_public_service
from ..services import PublicService

router = APIRouter(tags=["public"])


@router.get("/s/{slug_value}")
@router.head("/s/{slug_value}")
def redirect_slug(slug_value: str, request: Request, public_service: PublicService = Depends(get_public_service)):
    status_code, destination = public_service.resolve_redirect(slug_value, dict(request.query_params))
    return RedirectResponse(destination, status_code=status_code)


@router.get("/i/{slug_value}")
def slug_info(slug_value: str, public_service: PublicService = Depends(get_public_service)):
    return public_service.get_public_info(slug_value)
