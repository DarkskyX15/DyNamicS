# target-management Specification

## Purpose
定义多用户 target、slug、更新令牌与日志管理能力，包括资源归属、唯一性、target 模式、令牌生命周期和审计可见性。

## Requirements

### Requirement: 受 JWT 保护的管理 API
系统 MUST 提供带鉴权的管理 API，使用户在没有管理员权限时只能管理自己的 `slug`、`target`、更新令牌和日志。

#### Scenario: 普通用户访问自己的资源
- **WHEN** 一个已经通过鉴权且不是管理员的用户请求自己拥有的管理资源
- **THEN** 系统成功返回或修改这些资源

#### Scenario: 普通用户访问他人的资源
- **WHEN** 一个已经通过鉴权且不是管理员的用户请求其他用户拥有的管理资源
- **THEN** 系统拒绝访问

### Requirement: 全局唯一的 slug
系统 MUST 对 `slug` 值强制执行全局唯一约束。

#### Scenario: 创建唯一 slug
- **WHEN** 用户创建一个当前尚未被占用的 `slug`
- **THEN** 系统成功保存该 `slug`

#### Scenario: 拒绝重复 slug
- **WHEN** 用户创建或重命名一个已被占用的 `slug`
- **THEN** 系统以唯一性错误拒绝该请求

### Requirement: 用户拥有的 target 与 slug 管理
系统 MUST 允许一个用户创建多个 `slug`，并允许多个 `slug` 绑定到同一个 `target`。

#### Scenario: 多个 slug 指向同一个 target
- **WHEN** 用户将多个 `slug` 绑定到同一个 `target`
- **THEN** 系统成功保存所有这些绑定关系

#### Scenario: 一个用户拥有多个 slug
- **WHEN** 用户在自己的账户下创建多个 `slug`
- **THEN** 系统应分别保存每个 `slug` 以及它们各自的 target 绑定和跳转设置

### Requirement: target 模式同时支持静态与动态解析
系统 MUST 支持静态 `target`、主机动态更新 `target` 和完整 URL 动态更新 `target`。

#### Scenario: 创建静态 target
- **WHEN** 用户通过结构化 URL 字段创建一个静态 `target`
- **THEN** 系统将其保存为一个无需更新令牌即可解析的目标

#### Scenario: 创建主机动态更新 target
- **WHEN** 用户创建一个处于主机更新模式的 `target`
- **THEN** 系统将固定 URL 组成部分与当前主机值分开保存

#### Scenario: 创建完整 URL 动态更新 target
- **WHEN** 用户创建一个处于完整 URL 更新模式的 `target`
- **THEN** 系统以完整当前 URL 的形式保存并解析该目标

### Requirement: 更新令牌生命周期管理
系统 MUST 允许用户为自己拥有的 `target` 创建、禁用和撤销更新令牌。

#### Scenario: 创建更新令牌
- **WHEN** 用户为自己拥有的某个 `target` 创建更新令牌
- **THEN** 系统只返回一次令牌明文，并仅保存其受保护的表示形式用于后续校验

#### Scenario: 禁用令牌
- **WHEN** 用户禁用或撤销某个更新令牌
- **THEN** 之后使用该令牌发起的更新请求都必须被拒绝

### Requirement: 更新审计可见性
系统 MUST 记录并通过管理 API 暴露 `target` 的更新历史。

#### Scenario: 查看 target 更新历史
- **WHEN** 用户请求查看自己拥有的某个 `target` 的日志
- **THEN** 系统按时间倒序返回已记录的更新历史
