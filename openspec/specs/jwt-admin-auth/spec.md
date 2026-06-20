# jwt-admin-auth Specification

## Purpose
定义管理端 JWT access token 与 opaque refresh token 鉴权能力，包括登录、接口保护、会话续期与撤销要求。

## Requirements

### Requirement: 面向管理端的双令牌登录能力
系统 MUST 使用“JWT access token + opaque refresh token”的登录流程对管理用户进行鉴权。

#### Scenario: 使用有效凭证登录
- **WHEN** 用户向登录端点提交有效凭证
- **THEN** 系统签发用于管理端的 JWT access token
- **AND** 系统同时下发一个用于续期的 refresh token

#### Scenario: 使用无效凭证登录
- **WHEN** 用户提交无效凭证
- **THEN** 系统拒绝本次登录请求

### Requirement: 使用 access token 保护管理端接口
系统 MUST 要求所有受保护的管理 API 携带有效的 access token。

#### Scenario: 使用有效 access token 访问受保护接口
- **WHEN** 管理客户端携带有效 access token 调用受保护端点
- **THEN** 系统根据用户角色与资源归属对该请求进行授权

#### Scenario: 未携带有效 access token 访问受保护接口
- **WHEN** 管理客户端在没有有效 access token 的情况下调用受保护端点
- **THEN** 系统拒绝该请求

### Requirement: 基于 refresh token 的会话续期
系统 MUST 提供 refresh 流程，使管理客户端在 refresh token 仍然有效时，无需重新登录即可获取新的 access token。

#### Scenario: 使用有效 refresh token 续期
- **WHEN** 管理客户端提交一个有效的 refresh token
- **THEN** 系统签发新的 access token

#### Scenario: 使用无效 refresh token 续期
- **WHEN** 管理客户端提交一个无效、过期或已撤销的 refresh token
- **THEN** 系统拒绝本次续期请求

### Requirement: refresh token 由服务端保存哈希状态
系统 MUST 将 refresh token 视为服务器签发的随机 opaque token，并仅在服务端保存其哈希值和会话状态。

#### Scenario: 使用服务端保存的哈希校验 refresh token
- **WHEN** 管理客户端携带 refresh token 请求续期
- **THEN** 系统通过 refresh token 的哈希值查找对应会话状态
- **AND** 仅当该会话未过期且未撤销时才允许续期

#### Scenario: 服务端撤销 refresh 会话
- **WHEN** 用户登出、被禁用或发生需要强制失效会话的操作
- **THEN** 系统撤销对应的 refresh session
- **AND** 之后使用该 refresh token 发起的续期请求都必须被拒绝
