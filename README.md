
# DyNamicS

`DyNamicS` 现已重构为一个面向多用户的短链网关与动态目标管理平台。

它解决的问题不再是运行私有 DNS，而是通过稳定的 HTTP 入口路径为动态变化的服务目标提供可访问入口：

- `GET /s/<slug>`：将浏览器跳转到当前目标地址
- `GET /i/<slug>`：返回该 `slug` 当前公开可见的目标信息
- `POST /api/update/by-token/<token>`：供客户端按令牌更新目标主机或完整 URL

## 目录说明

- `backend`：基于 `FastAPI` 的后端服务，负责公开路由、JWT 管理鉴权、目标更新和持久化
- `frontend`：基于 `Vue + Vite` 的同域管理台，用于管理 `slug`、`target`、更新令牌和更新日志
- `client`：校园网自动登录客户端，可扩展为上报当前 IP 或完整 URL 至 DyNamicS 更新接口

## 当前实现能力

### 公开能力

- 公开跳转：`/s/<slug>`
- 公开信息查询：`/i/<slug>`

### 管理能力

- `JWT access token + opaque refresh token` 双令牌登录
- `target` CRUD
- `slug` CRUD
- target 更新令牌创建、禁用、删除
- target 更新日志查看

### 动态更新能力

- `dynamic_ip`：客户端只更新当前主机/IP
- `dynamic_url`：客户端更新完整 URL

## 运行方式

### 1. 后端

在 `backend/` 目录内运行后端，使用仓库根目录下的 `.venv`：

```powershell
..\.venv\Scripts\python.exe main.py
```

默认监听 `http://127.0.0.1:8000`。

也可以使用：

```powershell
..\.venv\Scripts\uvicorn.exe main:app --host 127.0.0.1 --port 8000
```

首次启动会自动初始化 `SQLite` 数据库，并创建默认管理员账号：

- 用户名：`admin`
- 密码：`admin123`

### 2. 前端

前端位于 `frontend/`，开发时可单独运行：

```powershell
npm install
npm run dev
```

生产构建：

```powershell
npm run build
```

构建产物位于 `frontend/dist`，后端会在同域下静态挂载该目录。

## 存储与迁移边界

当前版本使用 `SQLite`，但后端通过 Repo 层组织数据访问，后续迁移到 `PostgreSQL` 时应尽量保持：

- 路由层不直接依赖数据库细节
- 服务层只依赖 Repo 接口
- 持久化差异收束在 Repo 实现中
