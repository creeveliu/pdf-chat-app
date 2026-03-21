# Contributing

感谢你为 PDF Chat App 做贡献。

Thanks for contributing to PDF Chat App.

## Before You Start

- 先阅读根目录 [`README.md`](README.md)
- 使用 `.env.example` 创建本地环境变量文件，不要提交真实 `.env`
- 保持改动小而明确，优先在现有结构上增量修改

- Read the root [`README.md`](README.md)
- Create local env files from `.env.example`; do not commit real `.env` files
- Keep changes incremental and avoid broad refactors unless they are clearly justified

## Repository Boundaries

### Backend

- 路由放在 `backend/app/routes/`
- 业务逻辑放在 `backend/app/services/`
- `backend/app/main.py` 只负责应用初始化、middleware 和 router 注册

### Frontend

- 页面与路由放在 `frontend/src/app/`
- API 封装和请求逻辑放在 `frontend/src/lib/`
- 可复用 UI 放在 `frontend/src/components/`
- 不要把复杂请求逻辑重新塞回页面组件

## Product Constraints

- 保留 `/upload` 返回的 `document_id`，不要移除当前文档作用域问答机制
- 不要把多文档场景悄悄改成全局检索
- 不要移除基于文件内容 `SHA-256` 的文档去重
- 不要丢失 `contexts`、`citations`、`page_number`、`page_numbers`、`chunk_index`、`chunk_hash` 等引用元数据
- 前端默认通过 `/ask/stream` 渲染回答，不要无故回退成仅等待完整响应

## Local Setup

### Backend

```bash
cd backend
python3.10 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
./.venv/bin/python -m pytest -q
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run test
npm run lint
npm run build
```

## Pull Requests

- 为每个 PR 保持单一明确目标
- 在描述中说明动机、主要改动和验证方式
- 如果改动影响 UI、流式体验或引用展示，尽量附截图或说明交互变化
- 如果新增环境变量、目录或行为，请同步更新文档

- Keep each PR focused on one clear goal
- Describe motivation, main changes, and verification steps
- Update docs when behavior, setup, or environment variables change

## Runtime Data

`backend/data/uploads/` 和 `backend/data/index/` 是运行时目录，不要提交真实 PDF、索引文件或注册表内容。

`backend/data/uploads/` and `backend/data/index/` are runtime directories. Do not commit uploaded PDFs, index files, or generated registry contents.
