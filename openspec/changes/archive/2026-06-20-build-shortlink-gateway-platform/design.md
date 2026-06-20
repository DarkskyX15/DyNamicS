## Context

当前仓库中已经存在一个偏 Windows 场景的校园网客户端，它能够登录校园网并获取当前 IP，但原来面向动态 DNS 的后端和前端都尚未实现。本次变更将原计划中的 DNS 控制面替换为一个 HTTP 短链网关平台，在保留“提供稳定入口”这一核心价值的同时，显著简化系统的运行与维护。

新平台主要跨越四类关注点：

- 公开路由：`GET /s/{slug}` 与 `GET /i/{slug}`。
- 鉴权管理：用户、`slug`、`target`、令牌与日志管理。
- 动态更新：供现有客户端调用的基于令牌的目标更新能力。
- 存储与分层：当前运行在 `SQLite` 之上，同时保留未来迁移到 `PostgreSQL` 的边界。

约束条件：

- 前后端分离，技术栈为 `Vue` 与 `FastAPI`。
- 管理端鉴权使用 JWT。
- 持久化第一阶段使用 `SQLite`。
- 跳转仅面向浏览器友好场景，服务本身不是请求代理。
- `slug` 必须全局唯一。
- 一个用户可以拥有多个 `slug`，多个 `slug` 也可以指向同一个 `target`。

## Goals / Non-Goals

**Goals:**
- 提供一个基于全局唯一 `slug` 的公开跳转端点。
- 提供一个能够暴露 `slug` 当前公开目标状态的公开信息端点。
- 提供多用户的 `slug`、`target`、令牌与更新历史管理模型。
- 同时支持“仅更新主机/IP”和“更新完整 URL”两种动态更新模式。
- 对管理端使用 JWT，对更新客户端使用 target 级别令牌。
- 通过 Repo 接口隔离持久化细节，避免未来数据库迁移时牵动路由层。

**Non-Goals:**
- 不再实现 DNS 服务配置生成与下发。
- 不作为反向代理，也不承担浏览器之外负载的包体透传能力。
- 第一阶段不实现复杂的跨用户 `target` 共享工作流。
- 第一阶段不实现统计分析、基于健康检查的自动切换或复杂错误页系统。

## Decisions

### 1. 将产品重新定义为 HTTP 路由平台

Decision:
- 用应用层短链网关替代原本计划中的 DNS 后端与前端。

Rationale:
- 用户真正需要的是一个稳定入口，而不是 DNS 本身。
- 相较 DNS 编排，HTTP 跳转语义更容易部署、调试和演进。
- 现有客户端依然可以通过更新 `target` 的当前主机或 URL 继续发挥价值。

Alternatives considered:
- 保留 DNS 方案。未采用，因为它带来的运维复杂度更高，也不匹配当前代码基础。
- 同时支持 DNS 和 HTTP 两种入口。未采用，因为在控制面尚未建立前会无谓扩大范围。

### 2. 将 `slug` 与 `target` 建模为独立实体

Decision:
- `slug` 与 `target` 分开存储，二者通过 `slug -> target` 的多对一关系绑定。

Rationale:
- 产品要求同时满足 `user -> many slugs` 和 `many slugs -> one target`。
- 动态更新本质上属于目标状态，而不是每个 `slug` 各自独立维护。
- 这样可以把跳转行为、公开可见性与目标解析责任拆分清楚。

Alternatives considered:
- 将目标字段直接嵌入每个 `slug`。未采用，因为这会重复可变状态，并使多对一关系变得别扭。

### 3. 支持三种 `target` 模式

Decision:
- 引入 `static`、`dynamic_ip` 和 `dynamic_url` 三种 `target` 模式。

Rationale:
- `static` 用于手工维护的固定目标。
- `dynamic_ip` 对应现有客户端的真实能力，即只有当前主机/IP 会变化，而协议、端口和路径保持稳定。
- `dynamic_url` 则覆盖更通用的整条 URL 动态更新场景。

Resolution strategy:
- `static`：由结构化持久化字段拼装目标 URL。
- `dynamic_ip`：由结构化持久化字段加上最新主机值拼装目标 URL。
- `dynamic_url`：直接使用最新保存的完整 URL。

Alternatives considered:
- 只存完整 URL。未采用，因为仅更新主机的流程会变得笨重，也丢失了清晰的校验边界。
- 只支持主机更新。未采用，因为这会阻断更通用的动态目标场景。

### 4. 将公开跳转严格限制为浏览器友好行为

Decision:
- `/s/{slug}` 仅支持 `GET` 和 `HEAD`，其他方法返回 `405`。
- 每个 `slug` 可以配置自己的跳转状态码，但必须来自受限的浏览器友好集合。

Rationale:
- 系统明确不打算扮演代理或透明转发器。
- 限制方法可以防止用户误以为请求体、方法语义或非幂等行为会被完整保留。
- 每个 `slug` 单独配置跳转码，可以在不引入传输复杂度的前提下做兼容性调节。

Redirect code policy:
- 第一版仅接受 `302`、`307`、`308`。
- 新建 `slug` 默认使用 `302`。
- 第一阶段不开放 `301`，以避免难以回滚的浏览器缓存问题。

Alternatives considered:
- 所有方法都支持并统一返回 `307`。未采用，因为这会传达出系统并不打算保证的“传输保真性”。
- 全站统一一个跳转码。未采用，因为不同 `slug` 可能存在不同浏览器兼容性需求。

### 5. 保留并合并请求中的 query string

Decision:
- 将请求中的 query 参数合并进最终解析出的目标 URL，当键冲突时由请求参数覆盖目标默认参数。

Rationale:
- 用户会自然地期望共享短链接仍然可以承接临时参数。
- 让调用方显式传入的参数优先，是最不令人意外的规则。

Alternatives considered:
- 忽略请求中的 query 参数。未采用，因为这会削弱 `slug` 作为稳定入口的实用性。
- 让目标默认参数覆盖请求参数。未采用，因为这会让动态调用方的行为变得不直观。

### 6. 按调用方类型拆分鉴权体系

Decision:
- 面向人工管理端使用“JWT access token + 非 JWT refresh token”的双令牌方案。
- 面向机器更新端使用 target 级别更新令牌。

Rationale:
- 浏览器/后台工作流需要用户身份、资源归属和会话续期能力。
- 对于短期访问凭证，JWT 适合承载无状态的身份信息。
- 对于长期续期凭证，不信任 JWT 本身作为唯一事实来源，使用随机高熵 opaque token 并在服务端保存其状态，更容易实现撤销与失效控制。
- 更新客户端只需要被授权修改某一个 `target`。
- 将管理端续期凭证与 target 更新令牌拆开，可以显著缩小不同类型凭证泄露后的影响范围。

Token plan:
- `POST /api/auth/login` 颁发短期 JWT access token，并通过 `HttpOnly cookie` 下发长期 refresh token。
- access token 由前端保存在 `localStorage` 中，用于调用受保护的管理 API。
- refresh token 不是 JWT，而是服务器生成的随机高熵 opaque token。
- `POST /api/auth/refresh` 从 `HttpOnly cookie` 读取 refresh token，并在服务端完成哈希匹配与状态校验后签发新的 access token。
- 服务端不保存 refresh token 明文，只保存 `refresh_hash` 及过期、撤销等会话元数据。

Refresh session model:
- `refresh_sessions` 只保存最小必要状态，例如 `user_id`、`refresh_hash`、`expires_at`、`revoked_at`、`created_at`。
- refresh token 不做轮换，第一版仅要求支持续期、登出撤销、改密失效和账号禁用失效。

Alternatives considered:
- 将 refresh token 也实现为 JWT。未采用，因为这会把长期会话凭证建立在 JWT 自身之上，而当前方案更希望把长期会话状态完全收束到服务端控制中。
- 仅使用服务端 session。未采用，因为前端被明确设计为分离部署。

### 7. 使用 FastAPI 服务层与 Repo 层封装 SQLite

Decision:
- 后端按“路由层 -> 服务层 -> Repo 接口 -> SQLite 实现”进行分层。

Rationale:
- 项目当前阶段足够轻量，适合先以 `SQLite` 起步，但未来迁移到 `PostgreSQL` 已经是明确要求。
- Repo 接口可以把查询细节、事务边界和数据库差异从 API 处理函数中隔离出来。
- `FastAPI` 很适合承接类型化 schema、鉴权依赖与公开/管理 API 分层。

Repository boundaries:
- `UserRepo`
- `SlugRepo`
- `TargetRepo`
- `TargetUpdateTokenRepo`
- `UpdateLogRepo`
- `RefreshSessionRepo` 或等价的鉴权状态持久化抽象

Alternatives considered:
- 在 handler 中直接耦合 ORM session。未采用，因为这会增加持久化迁移成本，也会让服务层测试更困难。
- 一开始直接使用 PostgreSQL。未采用，因为当前仓库尚无后端实现，先用更低摩擦的起步方式更合适。

### 8. 使用独立的 Vue 管理前端

Decision:
- 使用独立的 Vue 管理界面，覆盖登录、`target` 管理、`slug` 管理、令牌管理和审计查看。

Rationale:
- 前后端分离是已经确定的技术方向。
- 资源型页面天然契合当前领域模型。
- 前端可以清晰引导用户完成“创建 target -> 创建 slug -> 生成 token -> 配置 updater”的主要流程。

Initial page scope:
- 登录页
- Dashboard
- `slug` 列表/详情页
- `target` 列表/详情页
- 令牌管理页
- 更新日志页

## Risks / Trade-offs

- [SQLite 写并发能力有限] -> 第一阶段控制部署规模，并通过 Repo 层隔离持久化行为，避免路由层依赖具体数据库特性。
- [access token 无状态而 refresh token 有状态，会让鉴权模型出现双轨复杂度] -> 将 access token 仅用于短期身份校验，将 refresh 逻辑集中在独立的 refresh session Repo 中。
- [用户可能误把跳转服务当作代理服务] -> 限制非 `GET`/`HEAD` 方法，并在 API 文档与前端文案中明确边界。
- [每个 slug 可独立配置跳转码会带来认知不一致] -> 限制允许值范围，并给出清晰的默认值 `302`。
- [多种动态 target 模式会增加校验复杂度] -> 将解析与校验逻辑集中到 target 服务层，而不是散落在 handler 中。
- [公开信息接口可能泄露敏感目标信息] -> `/i/{slug}` 只暴露明确允许公开的字段，并将禁用或私有状态统一表现为 `404`。

## Migration Plan

1. 建立后端项目结构、领域模型、Repo 接口以及用户、`target`、`slug`、令牌、日志和 refresh session 状态的数据表结构。
2. 先实现公开只读端点，以便尽早稳定 `slug` 解析和跳转规则。
3. 实现 JWT 鉴权与受保护的管理 API，包括 `target`、`slug`、令牌与日志管理。
4. 基于这些后端 API 实现 Vue 管理前端。
5. 实现基于令牌的更新端点，并让现有 `client/` 更新流程对接它们。
6. 更新仓库文档与 README，将项目定位切换为新的 HTTP 路由产品。

Rollback strategy:
- 由于当前后端与前端几乎都是未实现状态，这次发布的风险主要是增量式的。
- 如果部署失败，可以先停用公开路由与更新端点，同时保留客户端侧已有能力，待后端修正后再恢复。

## Open Questions

- `/i/{slug}` 是否总是暴露完整解析后的 URL，还是对某些模式只暴露更有限的公开投影？
- 管理员是否应当具备强制重新分配全局唯一 `slug` 的能力，还是只允许禁用冲突资源？
- 第一版部署预期是单个 FastAPI 应用只负责 API，还是要在同一次发布中明确 Vue 前端的静态部署方式？
