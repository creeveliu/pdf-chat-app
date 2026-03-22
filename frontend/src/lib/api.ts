export type UploadResponse = {
  document_id: string;
  already_exists: boolean;
  filename: string;
  text_length: number;
  page_count: number;
  preview: string;
  chunk_count?: number;
  embedding_count?: number;
  indexed_new_chunks?: number;
  expires_at?: string | null;
};

export type UploadStageEvent = {
  stage:
    | "upload_received"
    | "reusing_index"
    | "parsing_pdf"
    | "chunking"
    | "generating_embeddings"
    | "persisting_index";
  filename?: string;
  page_count?: number;
  chunk_count?: number;
  document_id?: string;
};

export type UploadEmbeddingProgressEvent = {
  current_batch: number;
  total_batches: number;
  completed_chunks: number;
  total_chunks: number;
};

export type UploadStreamHandlers = {
  onStage?: (event: UploadStageEvent) => void;
  onEmbeddingProgress?: (event: UploadEmbeddingProgressEvent) => void;
};

export type AskContext = {
  document_id: string;
  filename: string;
  chunk_id: number;
  chunk_index?: number;
  page_number?: number | null;
  page_numbers?: number[];
  chunk_hash?: string;
  text: string;
  score: number;
};

export type Citation = {
  document_id: string;
  filename: string;
  chunk_id: number;
  chunk_index: number;
  page_number?: number | null;
  page_numbers: number[];
};

export type AskResponse = {
  question: string;
  answer: string;
  contexts: AskContext[];
  citations: Citation[];
  top_k: number;
};

export type AskStreamStartEvent = {
  question: string;
  top_k: number;
};

export type AskStreamDeltaEvent = {
  delta: string;
};

export type AskStreamHandlers = {
  onStart?: (event: AskStreamStartEvent) => void;
  onDelta?: (event: AskStreamDeltaEvent) => void;
  onDone?: (response: AskResponse) => void;
};

type ApiErrorPayload = {
  detail?: string;
};

function getApiBaseUrl(): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!baseUrl) {
    throw new Error(
      "缺少 NEXT_PUBLIC_API_BASE_URL。请在 frontend/.env.local 或 frontend/.env 中配置后端地址。",
    );
  }

  return baseUrl.replace(/\/$/, "");
}

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as ApiErrorPayload;
    if (body.detail) {
      return body.detail;
    }
  } catch {
    // Ignore JSON parsing issues and fall back to a generic message.
  }

  return `请求失败，状态码 ${response.status}。`;
}

export async function uploadPdf(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}/upload`, {
      method: "POST",
      body: formData,
    });
  } catch {
    throw new Error("无法连接后端。请确认 FastAPI 服务已经启动。");
  }

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as UploadResponse;
}

export async function uploadPdfStream(
  file: File,
  handlers: UploadStreamHandlers,
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}/upload/stream`, {
      method: "POST",
      body: formData,
    });
  } catch {
    throw new Error("无法连接后端。请确认 FastAPI 服务已经启动。");
  }

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  if (!response.body) {
    throw new Error("浏览器不支持流式响应，无法接收上传进度。");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let donePayload: UploadResponse | null = null;

  function handleBlock(block: string) {
    const parsed = parseSseBlock(block);
    if (!parsed) {
      return;
    }

    const payload = JSON.parse(parsed.data) as
      | UploadStageEvent
      | UploadEmbeddingProgressEvent
      | UploadResponse
      | { detail?: string };

    if (parsed.event === "stage") {
      handlers.onStage?.(payload as UploadStageEvent);
      return;
    }

    if (parsed.event === "embedding_progress") {
      handlers.onEmbeddingProgress?.(payload as UploadEmbeddingProgressEvent);
      return;
    }

    if (parsed.event === "done") {
      donePayload = payload as UploadResponse;
      return;
    }

    if (parsed.event === "error") {
      const message = (payload as { detail?: string }).detail;
      throw new Error(message || "上传失败。");
    }
  }

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });

    let delimiterIndex = buffer.indexOf("\n\n");
    while (delimiterIndex >= 0) {
      const block = buffer.slice(0, delimiterIndex);
      buffer = buffer.slice(delimiterIndex + 2);
      handleBlock(block);
      delimiterIndex = buffer.indexOf("\n\n");
    }

    if (done) {
      break;
    }
  }

  if (buffer.trim()) {
    handleBlock(buffer);
  }

  if (!donePayload) {
    throw new Error("上传进度流提前结束，未收到完成结果。");
  }

  return donePayload;
}

export async function askQuestion(
  question: string,
  topK = 3,
  documentId?: string,
): Promise<AskResponse> {
  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
        document_id: documentId,
        top_k: topK,
      }),
    });
  } catch {
    throw new Error("无法连接后端。请确认 FastAPI 服务已经启动。");
  }

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as AskResponse;
}

function parseSseBlock(block: string): { event: string; data: string } | null {
  const lines = block
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length === 0) {
    return null;
  }

  let eventName = "";
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventName = line.slice("event:".length).trim();
      continue;
    }

    if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim());
    }
  }

  if (!eventName || dataLines.length === 0) {
    return null;
  }

  return {
    event: eventName,
    data: dataLines.join("\n"),
  };
}

export async function askQuestionStream(
  question: string,
  handlers: AskStreamHandlers,
  topK = 3,
  documentId?: string,
): Promise<AskResponse> {
  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}/ask/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
        document_id: documentId,
        top_k: topK,
      }),
    });
  } catch {
    throw new Error("无法连接后端。请确认 FastAPI 服务已经启动。");
  }

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  if (!response.body) {
    throw new Error("浏览器不支持流式响应，无法接收回答。");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let donePayload: AskResponse | null = null;

  function handleBlock(block: string) {
    const parsed = parseSseBlock(block);
    if (!parsed) {
      return;
    }

    const payload = JSON.parse(parsed.data) as
      | AskStreamStartEvent
      | AskStreamDeltaEvent
      | AskResponse
      | { detail?: string };

    if (parsed.event === "start") {
      handlers.onStart?.(payload as AskStreamStartEvent);
      return;
    }

    if (parsed.event === "delta") {
      handlers.onDelta?.(payload as AskStreamDeltaEvent);
      return;
    }

    if (parsed.event === "done") {
      donePayload = payload as AskResponse;
      handlers.onDone?.(donePayload);
      return;
    }

    if (parsed.event === "error") {
      const message = (payload as { detail?: string }).detail;
      throw new Error(message || "流式回答失败。");
    }
  }

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });

    let delimiterIndex = buffer.indexOf("\n\n");
    while (delimiterIndex >= 0) {
      const block = buffer.slice(0, delimiterIndex);
      buffer = buffer.slice(delimiterIndex + 2);
      handleBlock(block);
      delimiterIndex = buffer.indexOf("\n\n");
    }

    if (done) {
      break;
    }
  }

  if (buffer.trim()) {
    handleBlock(buffer);
  }

  if (!donePayload) {
    throw new Error("回答在完成前中断了，请重试。");
  }

  return donePayload;
}
