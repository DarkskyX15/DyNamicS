from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException, status

from ..config import settings
from ..models import User
from ..repos import RefreshSessionRepo, UserRepo
from ..utils import create_access_token, generate_refresh_token, password_hash, refresh_hash, utcnow, verify_password


class AuthService:
    def __init__(self, user_repo: UserRepo, refresh_session_repo: RefreshSessionRepo) -> None:
        self.user_repo = user_repo
        self.refresh_session_repo = refresh_session_repo

    def ensure_default_admin(self) -> None:
        if self.user_repo.get_by_username("admin") is None:
            self.user_repo.create_user("admin", password_hash("admin123"), role="admin")

    def login(self, username: str, password: str) -> tuple[User, str, str]:
        user = self.user_repo.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
        if user.status != "active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")
        access_token = create_access_token(user.id, user.username, user.role)
        refresh_token = generate_refresh_token()
        self.refresh_session_repo.create(
            user.id,
            refresh_hash(refresh_token),
            utcnow() + timedelta(days=settings.refresh_token_exp_days),
        )
        return user, access_token, refresh_token

    def refresh_access_token(self, refresh_token: str) -> tuple[User, str]:
        session = self.refresh_session_repo.get_by_hash(refresh_hash(refresh_token))
        if session is None or session.revoked_at is not None or session.expires_at < utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token 无效")
        user = self.user_repo.get_by_id(session.user_id)
        if user is None or user.status != "active":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不可用")
        return user, create_access_token(user.id, user.username, user.role)

    def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        session = self.refresh_session_repo.get_by_hash(refresh_hash(refresh_token))
        if session:
            self.refresh_session_repo.revoke(session.id)

    def get_current_user(self, user_id: int) -> User:
        user = self.user_repo.get_by_id(user_id)
        if user is None or user.status != "active":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不可用")
        return user
