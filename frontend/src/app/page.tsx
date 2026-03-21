"use client";

import { useState } from "react";

import { AnswerPanel } from "@/components/AnswerPanel";
import { QuestionPanel } from "@/components/QuestionPanel";
import { UploadPanel } from "@/components/UploadPanel";
import { askQuestion, type AskContext, uploadPdf, type UploadResponse } from "@/lib/api";

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState("还没有上传 PDF。");
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(3);
  const [askStatus, setAskStatus] = useState("索引完成后再提问。");
  const [askError, setAskError] = useState<string | null>(null);
  const [answer, setAnswer] = useState<string | null>(null);
  const [contexts, setContexts] = useState<AskContext[]>([]);
  const [isAsking, setIsAsking] = useState(false);

  async function handleUpload() {
    if (!selectedFile) {
      setUploadError("请先选择一个 PDF 文件。");
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setUploadResult(null);
    setUploadStatus("正在上传 PDF、解析文本并建立索引...");
    setAnswer(null);
    setContexts([]);
    setAskError(null);
    setAskStatus("等待新 PDF 建立索引后再提问。");

    try {
      const result = await uploadPdf(selectedFile);
      setUploadResult(result);
      setUploadStatus(`上传完成：${result.filename}`);
      setAskStatus("索引已就绪，现在可以提问了。");
    } catch (error) {
      const message = error instanceof Error ? error.message : "上传失败。";
      setUploadError(message);
      setUploadStatus("上传失败。");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleAsk() {
    if (!uploadResult?.document_id) {
      setAskError("请先上传并完成索引一个 PDF。");
      setAskStatus("还没有可提问的 PDF。");
      return;
    }

    setIsAsking(true);
    setAskError(null);
    setAskStatus("正在检索相关片段并生成回答...");

    try {
      const result = await askQuestion(question, topK, uploadResult.document_id);
      setAnswer(result.answer);
      setContexts(result.contexts);
      setAskStatus(`已命中 ${result.contexts.length} 个引用片段。`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "提问失败。";
      setAskError(message);
      setAskStatus("提问失败。");
      setAnswer(null);
      setContexts([]);
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#dbeafe,_#f8fafc_45%,_#e2e8f0_100%)] px-6 py-16 text-slate-950">
      <div className="mx-auto flex max-w-6xl flex-col gap-10">
        <section className="space-y-4">
          <p className="inline-flex rounded-full border border-sky-200 bg-white/80 px-3 py-1 text-sm font-medium text-sky-700 shadow-sm">
            PDF 问答应用
          </p>
          <div className="space-y-3">
            <h1 className="max-w-4xl text-5xl font-semibold tracking-tight text-balance">
              上传 PDF，建立索引，输入问题，并查看回答与引用片段。
            </h1>
            <p className="max-w-3xl text-lg leading-8 text-slate-600">
              这个页面直接连接 FastAPI 后端，覆盖完整本地链路：上传、建索引、提问、基于上下文的回答展示，以及引用片段查看。
            </p>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
          <UploadPanel
            fileName={selectedFile?.name ?? ""}
            isUploading={isUploading}
            uploadError={uploadError}
            uploadResult={uploadResult}
            uploadStatus={uploadStatus}
            onFileChange={setSelectedFile}
            onUpload={handleUpload}
          />
          <QuestionPanel
            askError={askError}
            askStatus={askStatus}
            canAsk={Boolean(uploadResult?.document_id)}
            isAsking={isAsking}
            question={question}
            topK={topK}
            onAsk={handleAsk}
            onQuestionChange={setQuestion}
            onTopKChange={(value) => {
              setTopK(Number.isNaN(value) ? 3 : Math.min(10, Math.max(1, value)));
            }}
          />
        </section>

        <AnswerPanel answer={answer} contexts={contexts} />
      </div>
    </main>
  );
}
