from __future__ import annotations

from typing import Generator

from fastapi import Depends, Header, HTTPException, Request, status

from .database import connection_scope
from .repos import RefreshSessionRepo, SlugRepo, TargetRepo, UpdateLogRepo, UpdateTokenRepo, UserRepo
from .services import AuthService, PublicService, TargetService
from .utils import decode_access_token


def get_connection() -> Generator:
    with connection_scope() as connection:
        yield connection


def get_user_repo(connection=Depends(get_connection)) -> UserRepo:
    return UserRepo(connection)


def get_slug_repo(connection=Depends(get_connection)) -> SlugRepo:
    return SlugRepo(connection)


def get_target_repo(connection=Depends(get_connection)) -> TargetRepo:
    return TargetRepo(connection)


def get_update_token_repo(connection=Depends(get_connection)) -> UpdateTokenRepo:
    return UpdateTokenRepo(connection)


def get_update_log_repo(connection=Depends(get_connection)) -> UpdateLogRepo:
    return UpdateLogRepo(connection)


def get_refresh_session_repo(connection=Depends(get_connection)) -> RefreshSessionRepo:
    return RefreshSessionRepo(connection)


def get_auth_service(
    user_repo: UserRepo = Depends(get_user_repo),
    refresh_session_repo: RefreshSessionRepo = Depends(get_refresh_session_repo),
) -> AuthService:
    return AuthService(user_repo, refresh_session_repo)


def get_target_service(
    slug_repo: SlugRepo = Depends(get_slug_repo),
    target_repo: TargetRepo = Depends(get_target_repo),
    update_token_repo: UpdateTokenRepo = Depends(get_update_token_repo),
    update_log_repo: UpdateLogRepo = Depends(get_update_log_repo),
) -> TargetService:
    return TargetService(slug_repo, target_repo, update_token_repo, update_log_repo)


def get_public_service(
    slug_repo: SlugRepo = Depends(get_slug_repo),
    target_repo: TargetRepo = Depends(get_target_repo),
    target_service: TargetService = Depends(get_target_service),
) -> PublicService:
    return PublicService(slug_repo, target_repo, target_service)


def get_current_user(
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少 access token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="access token 无效") from exc
    return auth_service.get_current_user(int(payload["sub"]))
