export type UploadResponse = {
  filename: string;
  text_length: number;
  page_count: number;
  preview: string;
  chunk_count?: number;
  embedding_count?: number;
};

export type AskContext = {
  document_id: string;
  filename: string;
  chunk_id: number;
  text: string;
  score: number;
};

export type AskResponse = {
  question: string;
  answer: string;
  contexts: AskContext[];
  top_k: number;
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

export async function askQuestion(question: string, topK = 3): Promise<AskResponse> {
  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
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
