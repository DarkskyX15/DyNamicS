from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import init_db
from .database import connection_scope
from .repos import RefreshSessionRepo, UserRepo
from .routers import auth_router, management_router, public_router, update_router
from .services import AuthService


def create_app() -> FastAPI:
    init_db()
    with connection_scope() as connection:
        AuthService(UserRepo(connection), RefreshSessionRepo(connection)).ensure_default_admin()

    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(management_router)
    app.include_router(update_router)
    app.include_router(public_router)

    if settings.frontend_dist.exists():
        assets_dir = settings.frontend_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        app.mount("/", StaticFiles(directory=settings.frontend_dist, html=True), name="frontend")

    return app
