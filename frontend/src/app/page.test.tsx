import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import Home from "@/app/page";
import { askQuestionStream, uploadPdf } from "@/lib/api";


vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");

  return {
    ...actual,
    uploadPdf: vi.fn(),
    askQuestionStream: vi.fn(),
  };
});

const mockedUploadPdf = vi.mocked(uploadPdf);
const mockedAskQuestionStream = vi.mocked(askQuestionStream);

describe("Home streaming chat", () => {
  it("updates the assistant message progressively and shows citations when complete", async () => {
    let continueStream: (() => void) | null = null;
    const streamFinished = new Promise<void>((resolve) => {
      continueStream = resolve;
    });

    mockedUploadPdf.mockResolvedValue({
      document_id: "doc-1",
      already_exists: false,
      filename: "guide.pdf",
      text_length: 1200,
      page_count: 12,
      preview: "preview",
      chunk_count: 6,
      indexed_new_chunks: 6,
    });

    mockedAskQuestionStream.mockImplementation(async (_question, handlers) => {
      handlers.onStart?.({ question: "这份 PDF 主要讲了什么？", top_k: 3 });
      handlers.onDelta?.({ delta: "这是一份 " });
      await streamFinished;
      handlers.onDelta?.({ delta: "PlayStation 指南。" });

      return {
        question: "这份 PDF 主要讲了什么？",
        answer: "这是一份 PlayStation 指南。",
        contexts: [
          {
            document_id: "doc-1",
            filename: "guide.pdf",
            chunk_id: 1,
            chunk_index: 1,
            page_number: 2,
            page_numbers: [2],
            text: "引用片段",
            score: 0.9,
          },
        ],
        citations: [
          {
            document_id: "doc-1",
            filename: "guide.pdf",
            chunk_id: 1,
            chunk_index: 1,
            page_number: 2,
            page_numbers: [2],
          },
        ],
        top_k: 3,
      };
    });

    const { container } = render(<Home />);

    const file = new File(["pdf"], "guide.pdf", { type: "application/pdf" });
    const fileInput = container.querySelector('input[type="file"]');
    expect(fileInput).not.toBeNull();

    fireEvent.change(fileInput as HTMLInputElement, {
      target: { files: [file] },
    });
    fireEvent.click(screen.getByRole("button", { name: "上传 PDF" }));

    await screen.findByText("上传完成：guide.pdf");

    fireEvent.change(screen.getByPlaceholderText("例如：这份说明书主要讲了什么？"), {
      target: { value: "这份 PDF 主要讲了什么？" },
    });
    fireEvent.click(screen.getByRole("button", { name: "发送问题" }));

    await screen.findByText("这是一份");
    expect(screen.queryByText("引用：第 2 页")).not.toBeInTheDocument();

    continueStream?.();

    await screen.findByText("这是一份 PlayStation 指南。");
    await waitFor(() => {
      expect(screen.getByText("引用：第 2 页")).toBeInTheDocument();
    });
  });

  it("keeps the chat column height constrained so the message list can scroll internally", () => {
    const { container } = render(<Home />);

    const contentGrid = container.querySelector(".xl\\:grid-cols-\\[300px_minmax\\(0\\,1fr\\)\\]");
    const chatColumn = container.querySelector(".xl\\:grid-cols-\\[300px_minmax\\(0\\,1fr\\)\\] > div");
    expect(contentGrid).toHaveClass("items-start");
    expect(chatColumn).toHaveClass("h-[78vh]", "min-h-0");
  });

  it("renders a lighter and more compact composer", () => {
    render(<Home />);

    const composerLabel = screen.getByText("输入你的问题");
    const composerSection = composerLabel.closest("section");
    const textarea = screen.getByRole("textbox");

    expect(composerSection).toHaveClass("bg-slate-100", "border-slate-200");
    expect(textarea).toHaveClass("min-h-24", "bg-white", "text-slate-900");
  });

  it("renders a more compact top header area", () => {
    render(<Home />);

    const title = screen.getByRole("heading", { name: "把 PDF 变成一个可连续对话的聊天助手。" });
    const headerSection = title.closest("section");
    const currentDocumentCard = screen.getByText("当前文档").closest("div");

    expect(headerSection).toHaveClass("px-5", "py-4");
    expect(title).toHaveClass("text-3xl");
    expect(currentDocumentCard).toHaveClass("px-3.5", "py-2.5");
  });
});
