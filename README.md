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
- [x] 前端上传表单接入
- [x] 前端提问与回答展示
- [x] 引用片段展示
- [x] 当前上传 PDF 作用域问答
- [x] 同一 PDF 内容哈希去重与索引复用
- [x] chunk metadata 与页码引用
- [x] 聊天式前端界面
- [x] 前端消息历史与引用展开

## Project Structure

```text
pdf-chat-app/
├── frontend/   # Next.js frontend
│   ├── src/components/  # Upload, chat, citations UI
│   ├── src/lib/         # Frontend API wrappers
│   ├── src/types/       # Frontend chat/domain types
│   └── src/test/        # Frontend test setup
├── backend/    # FastAPI backend
│   ├── app/routes/    # FastAPI routes
│   ├── app/services/  # PDF processing, dedupe, retrieval, QA
│   ├── data/uploads/  # Local uploaded PDF storage
│   └── data/index/    # FAISS indexes, chunk metadata, registry
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

前端环境变量：

```bash
cd frontend
cp .env.example .env.local
```

默认内容：

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

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

返回结果中会包含当前文档的 `document_id`，以及去重信息 `already_exists`、`indexed_new_chunks`。前端会自动保存这个值，并在后续提问时只检索这一次上传成功的 PDF。

基于已上传 PDF 提问：

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"question":"这份PDF主要讲了什么？","document_id":"<upload返回的document_id>","top_k":3}' \
  http://127.0.0.1:8000/ask
```

说明：
- 当后端只有一个索引文档时，`/ask` 可以不传 `document_id`
- 当后端已经存在多个 PDF 索引时，必须传 `document_id`，否则后端会返回明确错误，避免把旧文档内容混入回答
- `/ask` 返回的 `contexts` 已包含 `page_number`、`page_numbers`、`chunk_index` 等 metadata，`citations` 用于前端展示页码摘要

### Frontend Verification

```bash
cd frontend
npm run test
npm run lint
npm run build
```

当前前端体验：
- 上传区域与聊天区分离
- 连续多轮提问会保留消息历史
- 每条 AI 消息可展开查看引用片段、页码与 chunk 编号
- 未上传文档前会禁用提问输入框

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

1. 优化聊天界面的移动端体验与排版细节
2. 增加多文档切换或文档列表选择能力
3. 改善引用片段去重、排序和折叠体验
4. 增加历史问题持久化或会话恢复能力
5. 增加检索调试信息与更细致的错误提示
