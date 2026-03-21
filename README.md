# PDF Chat App

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Next.js](https://img.shields.io/badge/Next.js-16-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688)
![React](https://img.shields.io/badge/React-19-149ECA)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB)

中文 | English

一个用于上传 PDF、建立向量索引，并围绕当前文档进行连续问答的 Web 应用。

PDF Chat App is a monorepo web application for uploading PDFs, building vector indexes, and asking follow-up questions scoped to the current document.

## Features

- 上传 PDF 后自动解析文本、切分 chunk、生成 embedding，并写入 FAISS 索引
- 基于文件内容 `SHA-256` 做文档级去重，重复上传时复用已有索引
- 问答默认限定在当前 `document_id` 下，避免多文档互相污染
- 前端采用聊天式界面，支持多轮提问、流式回答和 Markdown 渲染
- 每条 AI 回答都返回引用上下文与页码信息，便于查看来源片段

- Automatic PDF parsing, chunking, embedding generation, and FAISS index persistence
- Document-level deduplication using file-content `SHA-256`
- Question answering scoped to the current `document_id`
- Chat-style frontend with streaming answers and Markdown rendering
- Citation metadata with page references and retrieved context snippets

## Screenshot

![PDF Chat App overview](docs/images/app-overview.png)

## Tech Stack

- Frontend: Next.js 16, React 19, Tailwind CSS 4, TypeScript
- Backend: FastAPI, Uvicorn, Python 3.10
- Vector store: FAISS
- PDF parsing: PyMuPDF
- LLM / embeddings: OpenAI-compatible APIs, currently configured for DashScope compatibility

## Repository Structure

```text
pdf-chat-app/
├── frontend/              # Next.js frontend
│   ├── src/app/           # App routes and page entry
│   ├── src/components/    # Chat, upload, citation UI
│   ├── src/lib/           # API wrappers and client utilities
│   ├── src/types/         # Frontend domain types
│   └── src/test/          # Frontend test setup
├── backend/               # FastAPI backend
│   ├── app/main.py        # App initialization and router registration
│   ├── app/routes/        # HTTP routes
│   ├── app/services/      # PDF, retrieval, embedding, QA services
│   ├── data/uploads/      # Runtime PDF storage
│   ├── data/index/        # Runtime FAISS indexes and document registry
│   └── tests/             # Backend tests
├── AGENTS.md              # Internal agent guidance for this repository
└── README.md
```

## Requirements

- Node.js 20+ and npm
- Python 3.10+
- A valid embedding API key
- A valid LLM API key if you want answer generation

## Quick Start

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd pdf-chat-app
```

### 2. Start the backend

```bash
cd backend
python3.10 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

默认地址 / Default URL: `http://127.0.0.1:8000`

健康检查 / Health check:

```bash
curl http://127.0.0.1:8000/health
```

### 3. Start the frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

默认地址 / Default URL: `http://localhost:3000`

## Environment Variables

前端和后端都只应提交 `.env.example`，不要提交真实 `.env` 文件。

Commit only `.env.example` files. Real `.env` files must stay untracked.

### Backend

Copy [`backend/.env.example`](backend/.env.example) to `backend/.env` and fill in real values:

```env
EMBEDDING_PROVIDER=dashscope
DASHSCOPE_API_KEY=your_dashscope_api_key_here
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_PROVIDER=dashscope
LLM_MODEL=qwen-plus
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

说明 / Notes:

- 如果使用 DashScope，可同时复用 `DASHSCOPE_API_KEY` 作为 embedding 和 LLM 的密钥来源
- 如果切换到 OpenAI-compatible provider，请根据 `backend/app/services/embedding.py` 和 `backend/app/services/llm.py` 中的规则设置 `OPENAI_API_KEY` 或 `LLM_API_KEY` / `EMBEDDING_API_KEY`
- `/upload` 在当前实现里会立即做索引，因此 embedding 配置在上传前就必须可用

- DashScope can be used as both the embedding and LLM provider through its OpenAI-compatible API
- For other providers, configure the matching API key variables expected by the backend services
- `/upload` immediately performs indexing, so embedding configuration must be valid before uploading files

### Frontend

Copy [`frontend/.env.example`](frontend/.env.example) to `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Usage

### Upload a PDF

```bash
curl -X POST \
  -F "file=@/absolute/path/to/your.pdf;type=application/pdf" \
  http://127.0.0.1:8000/upload
```

上传成功后会返回 `document_id`。前端会保存该值，并在后续提问时优先传给后端。

The upload response contains a `document_id`. The frontend stores it and sends it with follow-up questions.

### Ask a question

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"question":"这份 PDF 主要讲了什么？","document_id":"<document_id>","top_k":3}' \
  http://127.0.0.1:8000/ask
```

### Ask a question with streaming

```bash
curl -N -X POST \
  -H "Content-Type: application/json" \
  -d '{"question":"这份 PDF 主要讲了什么？","document_id":"<document_id>","top_k":3}' \
  http://127.0.0.1:8000/ask/stream
```

`/ask/stream` uses `text/event-stream` and emits `start`, `delta`, `done`, and `error` events.

## Runtime Data and Persistence

`backend/data/uploads/` 和 `backend/data/index/` 是运行时数据目录，不是源码目录。

`backend/data/uploads/` and `backend/data/index/` are runtime data directories, not source artifacts.

它们当前用于保存：

- 上传后的 PDF 文件
- FAISS 索引文件
- chunk metadata
- 文档注册表 `documents.json`

They currently store:

- uploaded PDFs
- FAISS index files
- chunk metadata
- the document registry `documents.json`

这意味着当前后端部署需要持久化磁盘。纯无状态、临时文件系统的 serverless 环境并不适合直接承载现有后端。

This means the backend needs persistent storage in production. Purely stateless serverless environments are not a good fit for the current backend without architectural changes.

## Verification

### Backend

```bash
cd backend
./.venv/bin/python -m pytest -q
```

### Frontend

```bash
cd frontend
npm run test
npm run lint
npm run build
```

## Known Limitations

- 当前默认问答语义是“围绕当前文档”，不是跨文档全局检索
- 上传和索引为同步链路，大 PDF 处理时间会较长
- 当前数据默认保存在本地磁盘，未接入对象存储或外部向量数据库
- 后端生产部署仍需额外配置 CORS 和持久化存储

- The default query scope is the current document, not cross-document retrieval
- Uploading and indexing are synchronous, so large PDFs take longer to process
- Runtime data is still stored on local disk
- Production deployment still requires CORS and persistent storage configuration

## Roadmap

- 优化聊天界面的移动端体验与输入交互
- 增加多文档列表、切换或历史上传记录
- 改善引用片段的去重、排序、折叠和阅读体验
- 增加更清晰的错误提示、空态提示和交互反馈

- Improve mobile chat layout and input experience
- Add document list, document switching, or upload history
- Improve citation deduplication, sorting, collapsing, and readability
- Add clearer error, empty-state, and interaction feedback

## Contributing

欢迎提交 issue 和 PR。开始之前请先阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

Issues and pull requests are welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) before contributing.

## Security

如果你发现了安全问题，请不要直接公开提交 issue，请参考 [`SECURITY.md`](SECURITY.md)。

If you find a security issue, please do not open a public issue first. See [`SECURITY.md`](SECURITY.md).

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).
