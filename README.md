# PDF Chat App

[English](README.en.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Next.js](https://img.shields.io/badge/Next.js-16-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688)
![React](https://img.shields.io/badge/React-19-149ECA)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB)

一个用于上传 PDF、建立向量索引，并围绕当前文档进行连续问答的 Web 应用。

线上前端访问地址：`https://frontend-sand-three-17.vercel.app/`

## 截图

![PDF Chat App 概览](docs/images/app-overview.png)

## 功能特性

- 上传 PDF 后自动解析文本、切分 chunk、生成 embedding，并写入 FAISS 索引
- 基于文件内容 `SHA-256` 做文档级去重，重复上传时复用已有索引
- 问答默认限定在当前 `document_id` 下，避免多文档互相污染
- 前端采用聊天式界面，支持多轮提问、流式回答和 Markdown 渲染
- 每条 AI 回答都返回引用上下文与页码信息，便于查看来源片段

## 技术栈

- Frontend: Next.js 16, React 19, Tailwind CSS 4, TypeScript
- Backend: FastAPI, Uvicorn, Python 3.10
- Vector store: FAISS
- PDF parsing: PyMuPDF
- LLM / embeddings: OpenAI-compatible APIs，当前默认按 DashScope 兼容方式配置

## 仓库结构

```text
pdf-chat-app/
├── frontend/              # Next.js 前端
│   ├── src/app/           # 页面与路由入口
│   ├── src/components/    # 聊天、上传、引用 UI
│   ├── src/lib/           # API 封装与客户端工具
│   ├── src/types/         # 前端领域类型
│   └── src/test/          # 前端测试初始化
├── backend/               # FastAPI 后端
│   ├── app/main.py        # 应用初始化与 router 注册
│   ├── app/routes/        # HTTP 路由
│   ├── app/services/      # PDF、检索、embedding、问答服务
│   ├── data/uploads/      # 运行时 PDF 存储
│   ├── data/index/        # 运行时 FAISS 索引与文档注册表
│   └── tests/             # 后端测试
├── AGENTS.md              # 仓库内部 agent 协作说明
└── README.md
```

## 环境要求

- Node.js 20+ 与 npm
- Python 3.10+
- 可用的 embedding API Key
- 若需要生成回答，还需要可用的 LLM API Key

## 快速开始

### 1. 克隆仓库

```bash
git clone <your-repo-url>
cd pdf-chat-app
```

### 2. 启动后端

```bash
cd backend
python3.10 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

默认地址：`http://127.0.0.1:8000`

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

### 3. 启动前端

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

默认地址：`http://localhost:3000`

## 环境变量

前端和后端都只应提交 `.env.example`，不要提交真实 `.env` 文件。

### 后端

将 [`backend/.env.example`](backend/.env.example) 复制为 `backend/.env`，再填写真实值：

```env
EMBEDDING_PROVIDER=dashscope
DASHSCOPE_API_KEY=your_dashscope_api_key_here
EMBEDDING_API_KEY=
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_PROVIDER=dashscope
LLM_API_KEY=
LLM_MODEL=qwen-plus
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=
OPENAI_BASE_URL=
FRONTEND_URL=http://localhost:3000
VERCEL_FRONTEND_URL=
CORS_ALLOW_ORIGINS=
CORS_ALLOW_ORIGIN_REGEX=
```

说明：

- 如果使用 DashScope，可同时复用 `DASHSCOPE_API_KEY` 作为 embedding 和 LLM 的密钥来源
- 如果切换到其他 OpenAI-compatible provider，请根据 `backend/app/services/embedding.py` 和 `backend/app/services/llm.py` 的读取规则设置 `OPENAI_API_KEY` 或 `LLM_API_KEY` / `EMBEDDING_API_KEY`
- `FRONTEND_URL` 和 `VERCEL_FRONTEND_URL` 会加入后端 CORS 白名单；`CORS_ALLOW_ORIGINS` 可继续追加多个域名，使用逗号分隔
- 如果需要匹配 Vercel preview 域名，可额外设置 `CORS_ALLOW_ORIGIN_REGEX`
- `/upload` 在当前实现里会立即做索引，因此 embedding 配置在上传前就必须可用

### 前端

将 [`frontend/.env.example`](frontend/.env.example) 复制为 `frontend/.env.local`：

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Vercel 生产环境应将该值设置为 Railway 后端公网地址，例如 `https://your-backend.up.railway.app`。

## 使用方式

### 上传 PDF

```bash
curl -X POST \
  -F "file=@/absolute/path/to/your.pdf;type=application/pdf" \
  http://127.0.0.1:8000/upload
```

上传成功后会返回 `document_id`。前端会保存该值，并在后续提问时优先传给后端。

### 发起提问

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"question":"这份 PDF 主要讲了什么？","document_id":"<document_id>","top_k":3}' \
  http://127.0.0.1:8000/ask
```

### 流式提问

```bash
curl -N -X POST \
  -H "Content-Type: application/json" \
  -d '{"question":"这份 PDF 主要讲了什么？","document_id":"<document_id>","top_k":3}' \
  http://127.0.0.1:8000/ask/stream
```

`/ask/stream` 使用 `text/event-stream`，会返回 `start`、`delta`、`done` 和 `error` 事件。

## 运行时数据与持久化

`backend/data/uploads/` 和 `backend/data/index/` 是运行时数据目录，不是源码目录。

它们当前用于保存：

- 上传后的 PDF 文件
- FAISS 索引文件
- chunk metadata
- 文档注册表 `documents.json`

这意味着当前后端部署需要可写磁盘。当前版本可以部署为“自己用的演示版”，但上传文件、FAISS 索引和 `documents.json` 都不保证长期持久化；如果 Railway 实例重建、重新部署或未挂载持久卷，历史数据可能丢失。

## 部署

### Frontend 部署到 Vercel

1. 在 Vercel 导入当前仓库。
2. 将 Root Directory 设为 `frontend/`。
3. Build Command 使用默认的 `npm run build`。
4. 配置环境变量：

```env
NEXT_PUBLIC_API_BASE_URL=https://your-backend.up.railway.app
```

5. 部署完成后，前端正式访问地址为 `https://frontend-sand-three-17.vercel.app/`。

### Backend 部署到 Railway

1. 在 Railway 为当前仓库新建服务。
2. 将 Root Directory 设为 `backend/`。
3. 启动命令使用：

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

仓库中也提供了 [`backend/Procfile`](backend/Procfile)，内容等价。

4. 至少配置以下环境变量：

```env
EMBEDDING_PROVIDER=dashscope
DASHSCOPE_API_KEY=your_dashscope_api_key_here
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_PROVIDER=dashscope
LLM_MODEL=qwen-plus
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
VERCEL_FRONTEND_URL=https://your-frontend.vercel.app
```

按实际 provider 选择性补充：

- `EMBEDDING_API_KEY`
- `LLM_API_KEY`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `CORS_ALLOW_ORIGINS`
- `CORS_ALLOW_ORIGIN_REGEX`

5. Railway 部署完成后，先访问 `/health` 检查服务是否正常，再把公网地址回填到 Vercel 的 `NEXT_PUBLIC_API_BASE_URL`。

### 推荐部署顺序

1. 先部署 Railway backend，拿到公网地址。
2. 再部署 Vercel frontend，并设置 `NEXT_PUBLIC_API_BASE_URL`。
3. 将 Vercel 的正式域名填回 Railway 的 `VERCEL_FRONTEND_URL`。
4. 如需支持 Vercel preview 域名，再配置 `CORS_ALLOW_ORIGIN_REGEX`。

## 验证命令

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

## 已知限制

- 当前默认问答语义是“围绕当前文档”，不是跨文档全局检索
- 上传和索引为同步链路，大 PDF 处理时间会较长
- 当前数据默认保存在本地磁盘，未接入对象存储或外部向量数据库
- Vercel + Railway 方案当前更适合作为演示版或个人使用，不保证上传文件与索引长期持久化

## Roadmap

- 优化聊天界面的移动端体验与输入交互
- 增加多文档列表、切换或历史上传记录
- 改善引用片段的去重、排序、折叠和阅读体验
- 增加更清晰的错误提示、空态提示和交互反馈

## 贡献

欢迎提交 issue 和 PR。开始之前请先阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

## 安全

如果你发现了安全问题，请不要直接公开提交 issue，请参考 [`SECURITY.md`](SECURITY.md)。

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).
