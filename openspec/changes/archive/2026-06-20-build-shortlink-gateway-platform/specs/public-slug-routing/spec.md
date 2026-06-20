## ADDED Requirements

### Requirement: 基于 slug 的公开跳转
系统必须提供一个公开端点，用于将全局唯一的 `slug` 解析到其当前目标，并返回面向浏览器使用的 HTTP 跳转响应。

#### Scenario: 跳转一个已启用的 slug
- **WHEN** 客户端对一个存在、已启用且绑定到可解析启用目标的 `slug` 发起 `GET /s/{slug}` 请求
- **THEN** 系统使用该 `slug` 配置的跳转状态码返回 HTTP 跳转响应
- **AND** `Location` 头指向解析后的目标 URL

#### Scenario: 拒绝跳转端点上的不受支持方法
- **WHEN** 客户端向 `/s/{slug}` 发送非 `GET` 且非 `HEAD` 的请求
- **THEN** 系统返回 `405 Method Not Allowed`

### Requirement: 每个 slug 可独立配置跳转行为
系统必须允许每个 `slug` 从受限的浏览器友好跳转状态码集合中保存自己的跳转码。

#### Scenario: 配置 slug 的专属跳转码
- **WHEN** 用户为某个 `slug` 配置了受支持的跳转状态码
- **THEN** 对该 `slug` 的请求应使用该配置值生成跳转响应

#### Scenario: 拒绝不受支持的跳转状态码
- **WHEN** 用户尝试保存集合之外的跳转状态码
- **THEN** 系统以校验错误拒绝该请求

### Requirement: 跳转时保留请求中的 query 参数
系统必须在构造跳转目标地址时保留传入请求的 query string。

#### Scenario: 合并目标参数与请求参数
- **GIVEN** 解析后的目标 URL 已经包含 query 参数
- **WHEN** 客户端请求 `/s/{slug}` 时又附加了额外的 query 参数
- **THEN** 最终跳转地址同时包含这两部分参数
- **AND** 当键冲突时，请求中的参数优先

### Requirement: 公开的 slug 信息查询端点
系统必须提供一个公开端点，用于返回某个 `slug` 当前可公开的目标信息。

#### Scenario: 返回当前 slug 的公开信息
- **WHEN** 客户端对一个存在、已启用且开放公开信息查询的 `slug` 发起 `GET /i/{slug}` 请求
- **THEN** 系统返回该 `slug` 的公开元数据以及当前解析出的目标信息

#### Scenario: 隐藏禁用或私有的 slug 信息
- **WHEN** 客户端查询一个不存在的 `slug`、已禁用的 `slug`，或未启用公开信息的 `slug`
- **THEN** 系统返回 `404 Not Found`

### Requirement: 对不可用目标进行安全失败处理
系统必须避免将请求跳转到一个已禁用或无法解析为合法目标 URL 的 `target`。

#### Scenario: slug 绑定的目标无法解析
- **WHEN** 某个 `slug` 存在，但其绑定的 `target` 已禁用或无法解析为合法 URL
- **THEN** 系统返回错误响应，而不是执行跳转
