"use client";

import { useState } from "react";

import { ChatInput } from "@/components/ChatInput";
import { ChatMessageList } from "@/components/ChatMessageList";
import { UploadPanel } from "@/components/UploadPanel";
import { askQuestion, uploadPdf, type UploadResponse } from "@/lib/api";
import type { ChatMessage } from "@/types/chat";


function createMessageId(prefix: string): string {
  return `${prefix}-${crypto.randomUUID()}`;
}

function createSystemMessage(content: string, tone: "default" | "success" | "error" = "default"): ChatMessage {
  return {
    id: createMessageId("system"),
    role: "system",
    content,
    createdAt: new Date().toISOString(),
    tone,
  };
}

function createUserMessage(content: string): ChatMessage {
  return {
    id: createMessageId("user"),
    role: "user",
    content,
    createdAt: new Date().toISOString(),
  };
}

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState("还没有上传 PDF。");
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    createSystemMessage("先上传一份 PDF。索引完成后，你就可以围绕当前文档连续提问。"),
  ]);
  const [askStatus, setAskStatus] = useState("文档就绪后可连续提问。");
  const [askError, setAskError] = useState<string | null>(null);
  const [isAsking, setIsAsking] = useState(false);

  async function handleUpload() {
    if (!selectedFile) {
      setUploadError("请先选择一个 PDF 文件。");
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setUploadStatus("正在上传 PDF、解析文本并建立索引...");
    setAskError(null);
    setAskStatus("等待新 PDF 建立索引后再提问。");

    try {
      const result = await uploadPdf(selectedFile);
      const isSameDocument = uploadResult?.document_id === result.document_id;
      const systemMessage = createSystemMessage(
        isSameDocument
          ? result.already_exists
            ? `已确认当前文档《${result.filename}》已存在，继续沿用现有索引。`
            : `已重新完成《${result.filename}》索引，现在可以继续提问。`
          : result.already_exists
            ? `已切换到《${result.filename}》，该文档已存在并复用了现有索引。`
            : `《${result.filename}》已上传并完成索引，聊天上下文已切换到当前文档。`,
        "success",
      );

      setUploadResult(result);
      setUploadStatus(`上传完成：${result.filename}`);
      setQuestion("");
      setMessages((currentMessages) =>
        isSameDocument ? [...currentMessages, systemMessage] : [systemMessage],
      );
      setAskStatus("索引已就绪，可以围绕当前文档连续提问。");
    } catch (error) {
      const message = error instanceof Error ? error.message : "上传失败。";
      setUploadError(message);
      setUploadStatus("上传失败。");
      setMessages((currentMessages) => [
        ...currentMessages,
        createSystemMessage(`上传失败：${message}`, "error"),
      ]);
    } finally {
      setIsUploading(false);
    }
  }

  async function handleAsk() {
    if (!uploadResult?.document_id) {
      setAskError("请先上传并完成索引一个 PDF。");
      setAskStatus("还没有可提问的 PDF。");
      setMessages((currentMessages) => [
        ...currentMessages,
        createSystemMessage("请先上传并完成索引一个 PDF，再开始聊天。", "error"),
      ]);
      return;
    }

    const normalizedQuestion = question.trim();
    if (!normalizedQuestion) {
      return;
    }

    setIsAsking(true);
    setAskError(null);
    setAskStatus("正在检索相关片段并生成回答...");
    setMessages((currentMessages) => [...currentMessages, createUserMessage(normalizedQuestion)]);
    setQuestion("");

    try {
      const result = await askQuestion(normalizedQuestion, 3, uploadResult.document_id);
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: createMessageId("assistant"),
          role: "assistant",
          content: result.answer,
          citations: result.citations,
          contexts: result.contexts,
          createdAt: new Date().toISOString(),
        },
      ]);
      setAskStatus(`已返回回答，并命中 ${result.contexts.length} 个引用片段。`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "提问失败。";
      setAskError(message);
      setAskStatus("提问失败。");
      setMessages((currentMessages) => [
        ...currentMessages,
        createSystemMessage(`提问失败：${message}`, "error"),
      ]);
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#dbeafe,_#f8fafc_38%,_#e2e8f0_100%)] px-6 py-10 text-slate-950">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <section className="rounded-[2rem] border border-white/80 bg-white/88 px-6 py-5 shadow-xl shadow-slate-200/70 backdrop-blur">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-3">
              <p className="inline-flex rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-sm font-medium text-sky-700 shadow-sm">
            PDF 问答应用
              </p>
              <div className="space-y-2">
                <h1 className="max-w-4xl text-4xl font-semibold tracking-tight text-balance">
                  把 PDF 变成一个可连续对话的聊天助手。
                </h1>
                <p className="max-w-3xl text-base leading-7 text-slate-600">
                  上传文档后，问题和回答会按消息流持续累积。每条 AI 回复都能展开查看引用片段与页码。
                </p>
              </div>
            </div>

            <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600 shadow-sm">
              <p className="text-xs uppercase tracking-[0.22em] text-slate-400">当前文档</p>
              <p className="mt-1 font-medium text-slate-900">
                {uploadResult ? uploadResult.filename : "还没有上传文档"}
              </p>
              <p className="mt-2 text-xs leading-5 text-slate-500">
                {uploadResult
                  ? `${uploadResult.page_count} 页 · ${uploadResult.chunk_count ?? 0} 个片段 · ${
                      uploadResult.already_exists ? "复用已有索引" : "新建索引"
                    }`
                  : "上传并完成索引后，可连续提问。"}
              </p>
            </div>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
          <UploadPanel
            fileName={selectedFile?.name ?? ""}
            isUploading={isUploading}
            uploadError={uploadError}
            uploadResult={uploadResult}
            uploadStatus={uploadStatus}
            onFileChange={setSelectedFile}
            onUpload={handleUpload}
          />

          <div className="flex min-h-[70vh] flex-col gap-4">
            <ChatMessageList isAsking={isAsking} messages={messages} />
            <ChatInput
              errorText={askError}
              isDisabled={!uploadResult?.document_id}
              isSending={isAsking}
              question={question}
              statusText={askStatus}
              onQuestionChange={setQuestion}
              onSend={handleAsk}
            />
          </div>
        </section>
      </div>
    </main>
  );
}
