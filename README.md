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
- [x] PDF 上传接口
- [x] PDF 文件本地存储与解析
- [ ] AI 问答链路
- [ ] 前端上传表单接入
- [ ] 聊天式前端交互

## Project Structure

```text
pdf-chat-app/
├── frontend/   # Next.js frontend
├── backend/    # FastAPI backend
│   ├── app/routes/    # FastAPI routes
│   ├── app/services/  # PDF processing and business logic
│   └── data/uploads/  # Local uploaded PDF storage
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

上传 PDF：

```bash
curl -X POST \
  -F "file=@/absolute/path/to/your.pdf;type=application/pdf" \
  http://127.0.0.1:8000/upload
```

## Next Plan

1. 在 `frontend` 接入 PDF 上传表单和上传状态管理
2. 为上传结果增加前端预览展示
3. 定义问答 API，开始串联文档与问题输入
4. 为后续 RAG 增加文本切分和索引准备层
5. 在前端补齐聊天界面与联调流程
