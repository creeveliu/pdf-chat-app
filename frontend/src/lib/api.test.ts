import { askQuestionStream } from "@/lib/api";


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
