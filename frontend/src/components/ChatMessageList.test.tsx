import { fireEvent, render, screen } from "@testing-library/react";

import { ChatMessageList } from "@/components/ChatMessageList";
import type { ChatMessage } from "@/types/chat";


describe("ChatMessageList", () => {
  it("renders user, system, and assistant messages with expandable citations", () => {
    const messages: ChatMessage[] = [
      {
        id: "system-1",
        role: "system",
        content: "文档已就绪，可以开始提问。",
        createdAt: "2026-03-21T10:00:00.000Z",
      },
      {
        id: "user-1",
        role: "user",
        content: "这份 PDF 主要讲了什么？",
        createdAt: "2026-03-21T10:01:00.000Z",
      },
      {
        id: "assistant-1",
        role: "assistant",
        content: "这是一份关于 PlayStation 5 的快速开始指南。",
        createdAt: "2026-03-21T10:01:05.000Z",
        citations: [
          {
            document_id: "doc-1",
            filename: "guide.pdf",
            chunk_id: 3,
            chunk_index: 3,
            page_number: 12,
            page_numbers: [12],
          },
        ],
        contexts: [
          {
            document_id: "doc-1",
            filename: "guide.pdf",
            chunk_id: 3,
            chunk_index: 3,
            page_number: 12,
            page_numbers: [12],
            text: "这是第 12 页的引用片段。",
            score: 0.123,
          },
        ],
      },
    ];

    const { container } = render(<ChatMessageList isAsking={false} messages={messages} />);

    expect(screen.getByText("文档已就绪，可以开始提问。")).toBeInTheDocument();
    expect(screen.getByText("这份 PDF 主要讲了什么？")).toBeInTheDocument();
    expect(screen.getByText("这是一份关于 PlayStation 5 的快速开始指南。")).toBeInTheDocument();
    expect(screen.getByText("引用：第 12 页")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "查看引用片段" }));

    expect(screen.getByText("这是第 12 页的引用片段。")).toBeInTheDocument();
    expect(screen.getAllByText(/片段 #3/)).not.toHaveLength(0);

    const chatRoot = container.firstElementChild;
    const scrollRegion = container.querySelector(".overflow-y-auto");
    expect(chatRoot).toHaveClass("min-h-0");
    expect(scrollRegion).toHaveClass("min-h-0");
    expect(screen.queryByRole("heading", { name: "围绕当前 PDF 连续提问" })).not.toBeInTheDocument();

    const userHeading = screen.getByText("你");
    const userBubble = userHeading.closest("article");
    expect(userBubble).toHaveClass("bg-slate-200", "text-slate-900");
  });

  it("renders assistant message content as markdown while keeping user messages as plain text", () => {
    const messages: ChatMessage[] = [
      {
        id: "user-1",
        role: "user",
        content: "**不要**被渲染成 Markdown",
        createdAt: "2026-03-21T10:01:00.000Z",
      },
      {
        id: "assistant-1",
        role: "assistant",
        content: [
          "## 回答摘要",
          "",
          "包含 **重点**、`inline code` 和列表：",
          "",
          "- 第一项",
          "- 第二项",
          "",
          "```ts",
          "const answer = 'markdown';",
          "```",
        ].join("\n"),
        createdAt: "2026-03-21T10:01:05.000Z",
        citations: [],
        contexts: [],
      },
    ];

    render(<ChatMessageList isAsking={false} messages={messages} />);

    expect(screen.getByText("**不要**被渲染成 Markdown")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "回答摘要" })).toBeInTheDocument();
    expect(screen.getByText("重点")).toContainHTML("strong");
    expect(screen.getByText("inline code").tagName).toBe("CODE");
    expect(screen.getByText("第一项")).toBeInTheDocument();
    expect(screen.getByText("第二项")).toBeInTheDocument();
    expect(screen.getByText("const answer = 'markdown';")).toBeInTheDocument();
  });

  it("does not force scroll to bottom after the user scrolls up during an active answer", () => {
    const { container, rerender } = render(
      <ChatMessageList
        isAsking={true}
        messages={[
          {
            id: "assistant-1",
            role: "assistant",
            content: "第一条回答，正在输出。",
            createdAt: "2026-03-21T10:01:05.000Z",
            citations: [],
            contexts: [],
            isStreaming: true,
          },
        ]}
      />,
    );

    const scrollRegion = container.querySelector(".overflow-y-auto");
    expect(scrollRegion).not.toBeNull();

    let scrollTopValue = 0;
    Object.defineProperty(scrollRegion as HTMLDivElement, "scrollHeight", {
      configurable: true,
      value: 1200,
    });
    Object.defineProperty(scrollRegion as HTMLDivElement, "clientHeight", {
      configurable: true,
      value: 400,
    });
    Object.defineProperty(scrollRegion as HTMLDivElement, "scrollTop", {
      configurable: true,
      get() {
        return scrollTopValue;
      },
      set(value: number) {
        scrollTopValue = value;
      },
    });
    const scrollToMock = vi.fn();
    Object.defineProperty(scrollRegion as HTMLDivElement, "scrollTo", {
      configurable: true,
      value: scrollToMock,
    });
    scrollToMock.mockClear();
    scrollTopValue = 800;
    fireEvent.scroll(scrollRegion as HTMLDivElement);
    scrollToMock.mockClear();

    scrollTopValue = 100;
    fireEvent.scroll(scrollRegion as HTMLDivElement);
    scrollToMock.mockClear();

    rerender(
      <ChatMessageList
        isAsking={true}
        messages={[
          {
            id: "assistant-1",
            role: "assistant",
            content: "第一条回答，正在继续输出。",
            createdAt: "2026-03-21T10:01:05.000Z",
            citations: [],
            contexts: [],
            isStreaming: true,
          },
        ]}
      />,
    );

    expect(scrollToMock).not.toHaveBeenCalled();
  });

  it("re-enables auto scroll when a new ask starts, then stops again after manual scroll", () => {
    const { container, rerender } = render(
      <ChatMessageList
        isAsking={false}
        messages={[
          {
            id: "assistant-1",
            role: "assistant",
            content: "旧回答",
            createdAt: "2026-03-21T10:01:05.000Z",
            citations: [],
            contexts: [],
          },
        ]}
      />,
    );

    const scrollRegion = container.querySelector(".overflow-y-auto");
    expect(scrollRegion).not.toBeNull();

    let scrollTopValue = 0;
    Object.defineProperty(scrollRegion as HTMLDivElement, "scrollHeight", {
      configurable: true,
      value: 1200,
    });
    Object.defineProperty(scrollRegion as HTMLDivElement, "clientHeight", {
      configurable: true,
      value: 400,
    });
    Object.defineProperty(scrollRegion as HTMLDivElement, "scrollTop", {
      configurable: true,
      get() {
        return scrollTopValue;
      },
      set(value: number) {
        scrollTopValue = value;
      },
    });

    const scrollToMock = vi.fn();
    Object.defineProperty(scrollRegion as HTMLDivElement, "scrollTo", {
      configurable: true,
      value: scrollToMock,
    });
    scrollToMock.mockClear();
    scrollTopValue = 800;
    fireEvent.scroll(scrollRegion as HTMLDivElement);
    scrollToMock.mockClear();

    scrollTopValue = 100;
    fireEvent.scroll(scrollRegion as HTMLDivElement);
    scrollToMock.mockClear();

    rerender(
      <ChatMessageList
        isAsking={true}
        messages={[
          {
            id: "assistant-1",
            role: "assistant",
            content: "旧回答",
            createdAt: "2026-03-21T10:01:05.000Z",
            citations: [],
            contexts: [],
          },
          {
            id: "assistant-2",
            role: "assistant",
            content: "新回答开头",
            createdAt: "2026-03-21T10:01:06.000Z",
            citations: [],
            contexts: [],
            isStreaming: true,
          },
        ]}
      />,
    );

    expect(scrollToMock).toHaveBeenCalledTimes(1);
    scrollTopValue = 800;
    fireEvent.scroll(scrollRegion as HTMLDivElement);
    scrollToMock.mockClear();

    scrollTopValue = 150;
    fireEvent.scroll(scrollRegion as HTMLDivElement);
    scrollToMock.mockClear();

    rerender(
      <ChatMessageList
        isAsking={true}
        messages={[
          {
            id: "assistant-1",
            role: "assistant",
            content: "旧回答",
            createdAt: "2026-03-21T10:01:05.000Z",
            citations: [],
            contexts: [],
          },
          {
            id: "assistant-2",
            role: "assistant",
            content: "新回答开头，继续输出。",
            createdAt: "2026-03-21T10:01:06.000Z",
            citations: [],
            contexts: [],
            isStreaming: true,
          },
        ]}
      />,
    );

    expect(scrollToMock).not.toHaveBeenCalled();
  });

  it("keeps auto scroll enabled after programmatic scrolling starts a new answer", () => {
    const { container, rerender } = render(
      <ChatMessageList
        isAsking={false}
        messages={[
          {
            id: "assistant-1",
            role: "assistant",
            content: "旧回答",
            createdAt: "2026-03-21T10:01:05.000Z",
            citations: [],
            contexts: [],
          },
        ]}
      />,
    );

    const scrollRegion = container.querySelector(".overflow-y-auto");
    expect(scrollRegion).not.toBeNull();

    let scrollTopValue = 0;
    Object.defineProperty(scrollRegion as HTMLDivElement, "scrollHeight", {
      configurable: true,
      value: 1200,
    });
    Object.defineProperty(scrollRegion as HTMLDivElement, "clientHeight", {
      configurable: true,
      value: 400,
    });
    Object.defineProperty(scrollRegion as HTMLDivElement, "scrollTop", {
      configurable: true,
      get() {
        return scrollTopValue;
      },
      set(value: number) {
        scrollTopValue = value;
      },
    });

    const scrollToMock = vi.fn();
    Object.defineProperty(scrollRegion as HTMLDivElement, "scrollTo", {
      configurable: true,
      value: scrollToMock,
    });
    scrollToMock.mockClear();
    scrollTopValue = 800;
    fireEvent.scroll(scrollRegion as HTMLDivElement);
    scrollToMock.mockClear();

    scrollTopValue = 100;
    fireEvent.scroll(scrollRegion as HTMLDivElement);
    scrollToMock.mockClear();

    rerender(
      <ChatMessageList
        isAsking={true}
        messages={[
          {
            id: "assistant-1",
            role: "assistant",
            content: "旧回答",
            createdAt: "2026-03-21T10:01:05.000Z",
            citations: [],
            contexts: [],
          },
          {
            id: "assistant-2",
            role: "assistant",
            content: "新回答开头",
            createdAt: "2026-03-21T10:01:06.000Z",
            citations: [],
            contexts: [],
            isStreaming: true,
          },
        ]}
      />,
    );

    expect(scrollToMock).toHaveBeenCalledTimes(1);
    scrollTopValue = 500;
    fireEvent.scroll(scrollRegion as HTMLDivElement);

    rerender(
      <ChatMessageList
        isAsking={true}
        messages={[
          {
            id: "assistant-1",
            role: "assistant",
            content: "旧回答",
            createdAt: "2026-03-21T10:01:05.000Z",
            citations: [],
            contexts: [],
          },
          {
            id: "assistant-2",
            role: "assistant",
            content: "新回答开头，继续输出。",
            createdAt: "2026-03-21T10:01:06.000Z",
            citations: [],
            contexts: [],
            isStreaming: true,
          },
        ]}
      />,
    );

    expect(scrollToMock).toHaveBeenCalledTimes(2);
  });
});
