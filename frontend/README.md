# Frontend

这是 `DyNamicS` 的管理前端，使用 `Vue 3 + Vite` 实现，部署时与后端同域，通过 `/api` 调用管理接口。

## 能力范围

- 登录与会话续期
- Dashboard 概览
- `target` 列表与编辑
- `slug` 列表与编辑
- 更新令牌管理
- 更新日志查看

## 开发

```powershell
npm install
npm run dev
```

## 构建

```powershell
npm run build
```

构建后产物输出到 `frontend/dist`，后端会自动挂载该目录作为静态管理台。
