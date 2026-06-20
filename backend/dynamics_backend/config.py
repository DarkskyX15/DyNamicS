from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    app_name: str = "DyNamicS"
    jwt_secret: str = os.environ.get("DYNAMICS_JWT_SECRET", "change-me-jwt-secret-for-local-development-32b")
    password_salt: str = os.environ.get("DYNAMICS_PASSWORD_SALT", "change-me-password-salt-for-local-development-32b")
    refresh_secret: str = os.environ.get("DYNAMICS_REFRESH_SECRET", "change-me-refresh-secret-for-local-development-32b")
    access_token_exp_minutes: int = int(os.environ.get("DYNAMICS_ACCESS_TOKEN_EXP_MINUTES", "15"))
    refresh_token_exp_days: int = int(os.environ.get("DYNAMICS_REFRESH_TOKEN_EXP_DAYS", "14"))
    database_path: Path = Path(os.environ.get("DYNAMICS_DATABASE_PATH", Path(__file__).resolve().parents[2] / "backend" / "dynamics.db"))
    frontend_dist: Path = Path(os.environ.get("DYNAMICS_FRONTEND_DIST", Path(__file__).resolve().parents[2] / "frontend" / "dist"))
    allowed_redirect_codes: tuple[int, ...] = (302, 307, 308)
    refresh_cookie_name: str = "dynamics_refresh_token"


settings = Settings()
