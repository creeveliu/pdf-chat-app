# Frontend

当前前端基于 Next.js 16、React 19、Tailwind CSS 4，负责 PDF 上传、聊天式问答、流式回答展示与引用片段展开。

## Local Development

启动开发环境：

```bash
npm run dev
```

默认访问地址：`http://localhost:3000`

如需连接本地后端，请先创建环境变量文件：

```bash
cp .env.example .env.local
```

默认内容：

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Verification

```bash
npm run test
npm run lint
npm run build
```

## Current UI Notes

- AI 聊天气泡支持 Markdown 渲染
- 回答默认通过流式接口逐步输出
- 每条 AI 消息支持展开查看引用片段、页码与 chunk 编号
- 用户手动滚动后，后续流式输出不会强制抢回滚动位置
