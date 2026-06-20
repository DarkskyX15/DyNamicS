## 1. 后端基础设施

- [x] 1.1 建立 `FastAPI` 后端项目结构，拆分路由、服务、Repo、Schema 和模型模块。
- [x] 1.2 添加后端依赖与配置，包括 `FastAPI`、JWT、密码哈希和 `SQLite` 访问支持。
- [x] 1.3 定义用户、`target`、`slug`、更新令牌、更新日志和 refresh session 状态的持久化模型与初始表结构。
- [x] 1.4 为用户、`slug`、`target`、更新令牌、更新日志和 refresh session 建立 Repo 接口及其 `SQLite` 实现。

## 2. 目标解析与公开路由

- [x] 2.1 实现 `static`、`dynamic_ip`、`dynamic_url` 三种 `target` 模式的领域逻辑，包括最终 URL 解析。
- [x] 2.2 实现 query string 合并逻辑，并确保请求参数优先于目标默认参数。
- [x] 2.3 实现 `/s/{slug}` 的公开 `GET` 与 `HEAD` 跳转处理，包括每个 `slug` 的跳转码校验与响应生成。
- [x] 2.4 实现 `/i/{slug}` 的公开信息返回逻辑，并正确处理可见性、禁用状态与不存在资源。

## 3. JWT 鉴权与授权

- [x] 3.1 实现凭证校验、密码哈希、短期 JWT access token 签发和 opaque refresh token 下发逻辑。
- [x] 3.2 实现 refresh session 的 `refresh_hash` 持久化、校验、撤销与续期流程。
- [x] 3.3 为受保护的管理路由加入鉴权依赖以及资源归属/管理员权限校验。

## 4. 管理 API

- [x] 4.1 实现用户自有 `target` 的 CRUD API，包括 target 模式和允许字段的校验。
- [x] 4.2 实现 `slug` 的 CRUD API，包括全局唯一校验、target 绑定、公开信息开关与每个 `slug` 的跳转码配置。
- [x] 4.3 实现 target 更新令牌管理 API，包括创建、禁用、撤销，并保证明文令牌只展示一次。
- [x] 4.4 实现 target 更新日志列表 API，供资源所有者与管理员查看。

## 5. 动态目标更新流程

- [x] 5.1 实现基于令牌鉴权的更新端点，支持仅更新主机和更新完整 URL 两类载荷。
- [x] 5.2 增加与模式对应的校验逻辑，使 `dynamic_ip` 只接受主机更新，`dynamic_url` 只接受完整 URL 更新。
- [x] 5.3 为成功的 target 更新持久化审计日志，包括旧快照、新快照和更新来源。

## 6. 前端管理应用

- [x] 6.1 搭建 `Vue` 前端应用骨架，并实现基于 JWT 会话的共享 API 客户端与鉴权状态管理。
- [x] 6.2 实现管理界面的登录与 token 刷新流程。
- [x] 6.3 实现 Dashboard、`slug` 列表/详情页和 `target` 列表/详情页。
- [x] 6.4 实现 target 的令牌管理页与更新日志页。

## 7. 客户端衔接与项目文档

- [x] 7.1 明确并记录现有 `client/` updater 如何调用新的基于令牌的 target 更新 API。
- [x] 7.2 更新仓库文档，说明新的短链网关架构、公开端点与管理技术栈。
- [x] 7.3 补充 Repo 抽象边界说明，为未来从 `SQLite` 迁移到 `PostgreSQL` 提供实现指引。
