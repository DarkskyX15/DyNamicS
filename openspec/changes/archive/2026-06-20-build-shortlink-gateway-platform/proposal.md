## Why

当前项目的原始定位是围绕校园网动态 IP 场景构建动态 DNS，但仓库中目前只有一个部分完成的客户端，后端与前端都尚未成型。将产品重构为短链接式的 HTTP 网关，可以保留“提供稳定入口”这一核心价值，同时显著降低运行 DNS 基础设施的复杂度。

## What Changes

- 将原计划中的动态 DNS 控制面替换为基于 `FastAPI` 和 `Vue` 的 HTTP 短链网关平台。
- 增加公开跳转端点，使全局唯一的 `slug` 可以将浏览器转发到动态或静态目标。
- 增加公开信息端点，使客户端与集成方能够读取某个 `slug` 当前解析出的目标状态。
- 增加带鉴权的管理 API 和前端界面，用于管理用户自己的 `slug`、`target`、更新令牌和更新历史。
- 增加基于令牌的 `target` 更新 API，使现有校园网客户端既可以更新当前主机/IP，也可以更新完整目标 URL。
- 在 `SQLite` 持久化之上引入 Repo 抽象层，以便后续迁移到 `PostgreSQL` 时尽量减少服务层改动。

## Capabilities

### New Capabilities
- `public-slug-routing`：公开浏览器跳转能力，以及公开的 `slug` 信息查询端点。
- `target-management`：面向多用户的 `target`、`slug` 绑定、跳转行为与更新令牌管理能力。
- `dynamic-target-updates`：面向动态目标的令牌鉴权更新能力，支持仅更新主机和更新完整 URL 两种模式。
- `jwt-admin-auth`：面向管理后台与前端会话生命周期的 JWT 鉴权能力。

### Modified Capabilities
- 无。

## Impact

- 会显著影响 `backend/`，因为当前后端基本尚未实现。
- 会新增一个用于管理界面的 `frontend/` 应用，而该目录目前在仓库中尚不存在。
- 会把 `README.md` 中描述的项目方向从 DNS 编排调整为 HTTP 跳转与信息路由。
- 需要新增持久化层、鉴权层、领域模型、API 分层，以及与现有 `client/` 更新流程的衔接路径。
