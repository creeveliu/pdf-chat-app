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

    render(<ChatMessageList isAsking={false} messages={messages} />);

    expect(screen.getByText("文档已就绪，可以开始提问。")).toBeInTheDocument();
    expect(screen.getByText("这份 PDF 主要讲了什么？")).toBeInTheDocument();
    expect(screen.getByText("这是一份关于 PlayStation 5 的快速开始指南。")).toBeInTheDocument();
    expect(screen.getByText("引用：第 12 页")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "查看引用片段" }));

    expect(screen.getByText("这是第 12 页的引用片段。")).toBeInTheDocument();
    expect(screen.getAllByText(/片段 #3/)).not.toHaveLength(0);
  });
});
