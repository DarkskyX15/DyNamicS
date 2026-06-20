## ADDED Requirements

### Requirement: 基于令牌鉴权的 target 更新
系统必须提供一个使用 target 级更新令牌进行鉴权的目标更新 API。

#### Scenario: 有效令牌成功更新 target
- **WHEN** 客户端使用一个有效、已启用且绑定到某个 `target` 的令牌调用更新端点
- **THEN** 系统接受该请求，并根据对应 `target` 的模式应用更新

#### Scenario: 无效令牌被拒绝
- **WHEN** 客户端使用缺失、无效、过期或已禁用的令牌调用更新端点
- **THEN** 系统拒绝该请求

### Requirement: dynamic host 模式下仅支持主机更新
系统必须支持对处于动态主机模式的 `target` 执行仅主机值更新。

#### Scenario: 更新当前主机值
- **GIVEN** 某个 `target` 被配置为动态主机更新模式
- **WHEN** 客户端提交一个合法的主机值
- **THEN** 系统更新该 `target` 的当前主机值
- **AND** 此后所有相关 `slug` 的解析结果都应使用更新后的主机值以及该 `target` 已配置的协议、端口、路径和默认 query

#### Scenario: 在主机模式下拒绝完整 URL 更新
- **GIVEN** 某个 `target` 被配置为动态主机更新模式
- **WHEN** 客户端提交完整 URL，而不是仅主机载荷
- **THEN** 系统以校验错误拒绝该请求

### Requirement: dynamic URL 模式下支持完整 URL 更新
系统必须支持对处于动态 URL 模式的 `target` 执行完整 URL 更新。

#### Scenario: 更新完整 URL 值
- **GIVEN** 某个 `target` 被配置为动态 URL 更新模式
- **WHEN** 客户端提交一个合法的完整 URL 载荷
- **THEN** 系统更新当前目标 URL

#### Scenario: 在完整 URL 模式下拒绝仅主机更新
- **GIVEN** 某个 `target` 被配置为动态 URL 更新模式
- **WHEN** 客户端只提交主机值
- **THEN** 系统以校验错误拒绝该请求

### Requirement: 记录 target 更新活动
系统必须记录 `target` 更新活动，以便后续审查。

#### Scenario: 持久化成功更新的日志
- **WHEN** 某次 `target` 更新成功
- **THEN** 系统保存一条审计记录，其中包含更新来源、更新前状态、更新后状态以及时间戳
