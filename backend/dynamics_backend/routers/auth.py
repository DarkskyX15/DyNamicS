from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response

from ..config import settings
from ..dependencies import get_auth_service, get_current_user
from ..schemas import AccessTokenResponse, LoginRequest, MessageResponse, UserResponse
from ..services import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/api/auth",
        max_age=settings.refresh_token_exp_days * 24 * 60 * 60,
    )


@router.post("/login", response_model=AccessTokenResponse)
def login(payload: LoginRequest, response: Response, auth_service: AuthService = Depends(get_auth_service)):
    user, access_token, refresh_token = auth_service.login(payload.username, payload.password)
    _set_refresh_cookie(response, refresh_token)
    return AccessTokenResponse(
        access_token=access_token,
        user=UserResponse(id=user.id, username=user.username, role=user.role, status=user.status),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(request: Request, auth_service: AuthService = Depends(get_auth_service)):
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    user, access_token = auth_service.refresh_access_token(refresh_token or "")
    return AccessTokenResponse(
        access_token=access_token,
        user=UserResponse(id=user.id, username=user.username, role=user.role, status=user.status),
    )


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response, auth_service: AuthService = Depends(get_auth_service)):
    auth_service.logout(request.cookies.get(settings.refresh_cookie_name))
    response.delete_cookie(settings.refresh_cookie_name, path="/api/auth")
    return MessageResponse(message="已退出登录")


@router.get("/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    return UserResponse(id=user.id, username=user.username, role=user.role, status=user.status)
