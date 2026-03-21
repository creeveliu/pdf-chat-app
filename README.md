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
- [x] 文本 chunking
- [x] Embedding 生成
- [x] FAISS 向量索引落盘
- [x] 阿里百炼 OpenAI 兼容 embedding 支持
- [x] 检索接口
- [x] AI 问答链路
- [ ] 前端上传表单接入
- [ ] 聊天式前端交互

## Project Structure

```text
pdf-chat-app/
├── frontend/   # Next.js frontend
├── backend/    # FastAPI backend
│   ├── app/routes/    # FastAPI routes
│   ├── app/services/  # PDF processing and business logic
│   ├── data/uploads/  # Local uploaded PDF storage
│   └── data/index/    # FAISS indexes and chunk metadata
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

基于已上传 PDF 提问：

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"question":"这份PDF主要讲了什么？","top_k":3}' \
  http://127.0.0.1:8000/ask
```

### Embedding Config

`/upload` 在当前实现里会立即做 chunk、embedding 和 FAISS 建索引，因此需要先配置 embedding provider。

如果使用阿里百炼：

1. 复制配置模板
```bash
cd backend
cp .env.example .env
```

2. 在 `backend/.env` 中填写：
```env
EMBEDDING_PROVIDER=dashscope
DASHSCOPE_API_KEY=你的阿里百炼API Key
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

说明：
- 当前后端应使用百炼官方 OpenAI 兼容 embedding 地址 `https://dashscope.aliyuncs.com/compatible-mode/v1`
- 不建议使用截图里的 `https://coding.dashscope.aliyuncs.com/v1` 作为 embedding 接口地址
- 百炼 embedding 接口当前实现按每批最多 `10` 条输入发送请求，避免兼容层的批量限制

## Next Plan

1. 在 `frontend` 接入 PDF 上传表单和上传状态管理
2. 为上传结果增加前端预览展示
3. 在前端接入提问输入框与回答展示
4. 增加引用片段的可视化展示与交互
5. 在前端补齐完整上传-提问联调流程
