import { askQuestionStream, uploadPdfStream } from "@/lib/api";


function buildStreamResponse(chunks: string[]): Response {
  const encoder = new TextEncoder();

  return new Response(
    new ReadableStream({
      start(controller) {
        for (const chunk of chunks) {
          controller.enqueue(encoder.encode(chunk));
        }
        controller.close();
      },
    }),
    {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
      },
    },
  );
}

describe("askQuestionStream", () => {
  it("parses SSE events and returns the final payload", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://127.0.0.1:8000");

    const fetchMock = vi.fn().mockResolvedValue(
      buildStreamResponse([
        'event: start\ndata: {"question":"这份 PDF 主要讲了什么？","top_k":3}\n\n',
        'event: delta\ndata: {"delta":"这是一份 "}\n\n',
        'event: delta\ndata: {"delta":"PlayStation 指南。"}\n\n',
        'event: done\ndata: {"question":"这份 PDF 主要讲了什么？","answer":"这是一份 PlayStation 指南。","contexts":[{"document_id":"doc-1","filename":"guide.pdf","chunk_id":1,"chunk_index":1,"page_number":2,"page_numbers":[2],"text":"引用片段","score":0.9}],"citations":[{"document_id":"doc-1","filename":"guide.pdf","chunk_id":1,"chunk_index":1,"page_number":2,"page_numbers":[2]}],"top_k":3}\n\n',
      ]),
    );
    vi.stubGlobal("fetch", fetchMock);

    const events: string[] = [];
    const result = await askQuestionStream(
      "这份 PDF 主要讲了什么？",
      {
        onStart(event) {
          events.push(`start:${event.top_k}`);
        },
        onDelta(event) {
          events.push(`delta:${event.delta}`);
        },
      },
      3,
      "doc-1",
    );

    expect(result.answer).toBe("这是一份 PlayStation 指南。");
    expect(result.citations).toHaveLength(1);
    expect(events).toEqual([
      "start:3",
      "delta:这是一份 ",
      "delta:PlayStation 指南。",
    ]);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/ask/stream",
      expect.objectContaining({
        method: "POST",
      }),
    );
  });
});

describe("uploadPdfStream", () => {
  it("parses staged SSE events and returns the final upload payload", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://127.0.0.1:8000");

    const fetchMock = vi.fn().mockResolvedValue(
      buildStreamResponse([
        'event: stage\ndata: {"stage":"upload_received","filename":"guide.pdf"}\n\n',
        'event: stage\ndata: {"stage":"parsing_pdf","filename":"guide.pdf"}\n\n',
        'event: embedding_progress\ndata: {"current_batch":1,"total_batches":2,"completed_chunks":3,"total_chunks":6}\n\n',
        'event: done\ndata: {"document_id":"doc-1","already_exists":false,"filename":"guide.pdf","text_length":1200,"page_count":12,"preview":"preview","chunk_count":6,"indexed_new_chunks":6,"embedding_count":6}\n\n',
      ]),
    );
    vi.stubGlobal("fetch", fetchMock);

    const events: string[] = [];
    const file = new File(["pdf"], "guide.pdf", { type: "application/pdf" });
    const result = await uploadPdfStream(file, {
      onStage(event) {
        events.push(`stage:${event.stage}`);
      },
      onEmbeddingProgress(event) {
        events.push(`embedding:${event.current_batch}/${event.total_batches}`);
      },
    });

    expect(result.filename).toBe("guide.pdf");
    expect(result.embedding_count).toBe(6);
    expect(events).toEqual([
      "stage:upload_received",
      "stage:parsing_pdf",
      "embedding:1/2",
    ]);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/upload/stream",
      expect.objectContaining({
        method: "POST",
      }),
    );
  });
});
