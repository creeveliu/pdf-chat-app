# AGENTS.md

## Project Stage

当前项目处于第 1 阶段：基础脚手架已完成，前后端可启动，正在开发 PDF 上传功能。此阶段目标是先打通上传链路，再进入 PDF 解析与 AI 问答实现。

## Source of Truth

- 前端目录：`frontend/`
- 后端目录：`backend/`
- 当前后端入口：`backend/app/main.py`
- 当前优先任务：PDF 上传功能

## Engineering Rules

### 1. Keep routes and services separated

新增功能时必须保持路由层和服务层分离，不要把业务逻辑直接堆在入口文件或页面文件里。

- Backend:
  - 路由放在 `backend/app/routes/`
  - 业务逻辑放在 `backend/app/services/`
  - `main.py` 只负责应用初始化、middleware、router 注册
- Frontend:
  - 页面与路由放在 `frontend/src/app/`
  - 与后端交互、上传请求、API 封装放在 `frontend/src/services/`
  - 不要在页面组件里直接堆积复杂请求逻辑

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

当前正在开发 PDF 上传功能，后续 agent 应优先完成以下链路：

1. 前端上传组件
2. 后端上传接口
3. 文件落盘或临时存储
4. 上传成功后的基础返回结构

在 PDF 上传链路完成之前，不要提前做大规模 AI 对话层重构。

## Preferred Near-Term Structure

建议后续按以下结构扩展：

```text
backend/app/
├── main.py
├── routes/
└── services/

frontend/src/
├── app/
└── services/
```

## Working Style for Future Agents

- 先读现有结构，再改代码
- 保持变更小而可验证
- 优先补齐当前能力，不提前铺过多抽象
- 若新增模块，命名直接、职责单一
