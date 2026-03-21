# AGENTS.md

## Project Stage

当前项目处于第 5 阶段：前后端主链路已经打通，并且问答已按“当前上传的 PDF”做文档作用域隔离。用户现在可以在前端上传 PDF、等待建索引、输入问题、查看回答和引用片段。当前目标是优化交互体验、引用片段展示和整体可用性。

## Source of Truth

- 前端目录：`frontend/`
- 后端目录：`backend/`
- 当前后端入口：`backend/app/main.py`
- 当前优先任务：前端体验优化、多文档交互完善、引用片段可读性提升

## Engineering Rules

### 1. Keep routes and services separated

新增功能时必须保持路由层和服务层分离，不要把业务逻辑直接堆在入口文件或页面文件里。

- Backend:
  - 路由放在 `backend/app/routes/`
  - 业务逻辑放在 `backend/app/services/`
  - `main.py` 只负责应用初始化、middleware、router 注册
- Frontend:
  - 页面与路由放在 `frontend/src/app/`
  - 与后端交互、上传请求、API 封装放在 `frontend/src/lib/`
  - 不要在页面组件里直接堆积复杂请求逻辑

### 1.1. Preserve document scoping in Q&A

- `/upload` 返回的 `document_id` 是当前问答链路的重要状态，不要删除
- 前端提问时必须优先传当前上传成功的 `document_id`
- 后端多文档场景下不能默认做全局检索，避免旧 PDF 污染当前回答
- 如果后续要支持“跨文档检索”，应作为显式功能设计，不要悄悄改变当前语义

### 2. Do not refactor casually

- 不要为了“更优雅”随意改目录结构
- 不要大范围重命名文件、模块或路径
- 不要在没有明确收益的情况下替换现有栈
- 不要引入额外基础设施，除非当前任务明确需要

当前仓库还在搭骨架阶段，优先保证功能增量清晰、变更范围小、便于后续 agent 接力。

### 3. Make incremental changes

- 一次只推进一个明确目标
- 新增文件优先小而明确
- 修改时优先复用现有入口和目录
- 完成功能后补最基本的运行验证

## Current Development Focus

后续 agent 应优先完成以下链路：

1. 优化问答页面布局和响应式表现
2. 增加多 PDF 文档列表、当前文档切换或历史上传记录
3. 改善引用片段的去重、排序和可读性
4. 完善错误提示、空态提示和交互反馈
5. 若需要，再逐步演进为聊天式界面

前后端主链路已经存在，不要重复改写上传、索引、检索、问答的基本流程，优先在现有结构上增量优化。

## Preferred Near-Term Structure

建议后续按以下结构扩展：

```text
backend/app/
├── main.py
├── routes/
└── services/

frontend/src/
├── app/
├── components/
└── lib/
```

## Working Style for Future Agents

- 先读现有结构，再改代码
- 保持变更小而可验证
- 优先补齐当前能力，不提前铺过多抽象
- 若新增模块，命名直接、职责单一
- 不要回退已经完成的 `/upload` 能力或把逻辑重新塞回 `main.py`
- 不要回退已经完成的阿里百炼兼容 embedding 支持或 FAISS 落盘结构
- 不要回退已经完成的 `/ask` 检索与问答能力
- 不要回退已经完成的 `document_id` 作用域提问机制
- 不要把前端请求逻辑重新塞回单个页面文件，保持 `components/` 和 `lib/api.ts` 分层
