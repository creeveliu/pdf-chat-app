# PDF Chat App

一个用于上传 PDF 并基于文档内容进行 AI 问答的 Web 应用。当前仓库采用 monorepo 结构，前端与后端分离，便于并行开发和后续持续迭代。

## Tech Stack

- Frontend: Next.js 16, React 19, Tailwind CSS 4, TypeScript
- Backend: FastAPI, Uvicorn, Python 3.10
- Repo: Monorepo, Git

## Current Progress

- [x] Monorepo 仓库初始化完成
- [x] Next.js 前端脚手架完成
- [x] FastAPI 后端脚手架完成
- [x] 前后端本地启动验证完成
- [ ] PDF 上传接口
- [ ] PDF 文件存储与解析
- [ ] AI 问答链路
- [ ] 聊天式前端交互

## Project Structure

```text
pdf-chat-app/
├── frontend/   # Next.js frontend
├── backend/    # FastAPI backend
├── README.md
└── AGENTS.md
```

## Run Locally

### Frontend

```bash
cd frontend
npm run dev
```

默认地址：`http://localhost:3000`

### Backend

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload
```

默认地址：`http://127.0.0.1:8000`

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

## Next Plan

1. 实现前端 PDF 上传表单与基础状态管理
2. 在 FastAPI 中新增上传路由与文件保存逻辑
3. 接入 PDF 文本提取流程
4. 定义问答 API，串联上传文档与提问流程
5. 在前端补齐聊天界面与请求联调
