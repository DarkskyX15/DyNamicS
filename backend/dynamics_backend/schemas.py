from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


TargetMode = Literal["static", "dynamic_ip", "dynamic_url"]


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=3, max_length=128)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    status: str


class TargetBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    mode: TargetMode
    scheme: str | None = None
    host: str | None = None
    port: int | None = Field(default=None, ge=1, le=65535)
    base_path: str | None = None
    default_query: dict[str, str] = Field(default_factory=dict)
    full_url: str | None = None
    enabled: bool = True

    @field_validator("scheme")
    @classmethod
    def validate_scheme(cls, value: str | None) -> str | None:
        if value is None:
            return value
        lowered = value.lower()
        if lowered not in {"http", "https"}:
            raise ValueError("scheme 仅支持 http 或 https")
        return lowered


class TargetCreate(TargetBase):
    pass


class TargetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    mode: TargetMode | None = None
    scheme: str | None = None
    host: str | None = None
    port: int | None = Field(default=None, ge=1, le=65535)
    base_path: str | None = None
    default_query: dict[str, str] | None = None
    full_url: str | None = None
    enabled: bool | None = None


class TargetResponse(TargetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_user_id: int
    last_updated_by_type: str
    resolved_url: str | None = None
    created_at: datetime
    updated_at: datetime
    slug_count: int = 0


class SlugBase(BaseModel):
    slug: str = Field(min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
    target_id: int
    enabled: bool = True
    info_public_enabled: bool = True
    redirect_code: int = 302
    description: str = Field(default="", max_length=500)


class SlugCreate(SlugBase):
    pass


class SlugUpdate(BaseModel):
    slug: str | None = Field(default=None, min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
    target_id: int | None = None
    enabled: bool | None = None
    info_public_enabled: bool | None = None
    redirect_code: int | None = None
    description: str | None = Field(default=None, max_length=500)


class SlugResponse(BaseModel):
    id: int
    slug: str
    owner_user_id: int
    target_id: int
    enabled: bool
    info_public_enabled: bool
    redirect_code: int
    description: str
    created_at: datetime
    updated_at: datetime


class UpdateTokenCreate(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    expires_at: datetime | None = None


class UpdateTokenResponse(BaseModel):
    id: int
    target_id: int
    label: str
    enabled: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime
    plain_token: str | None = None


class UpdateTokenToggle(BaseModel):
    enabled: bool


class UpdateLogResponse(BaseModel):
    id: int
    target_id: int
    source_type: str
    old_snapshot: dict
    new_snapshot: dict
    created_at: datetime


class PublicInfoResponse(BaseModel):
    slug: str
    enabled: bool
    mode: TargetMode
    target_url: str
    updated_at: datetime
    description: str


class UpdateTargetRequest(BaseModel):
    host: str | None = None
    url: str | None = None


class MessageResponse(BaseModel):
    message: str


class DashboardResponse(BaseModel):
    slug_count: int
    target_count: int
    token_count: int
    latest_targets: list[TargetResponse]


AccessTokenResponse.model_rebuild()
