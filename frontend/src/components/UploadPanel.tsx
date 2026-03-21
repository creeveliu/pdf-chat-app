import { useState, type DragEvent } from "react";

import type { UploadResponse } from "@/lib/api";

type UploadPanelProps = {
  fileName: string;
  isUploading: boolean;
  uploadStatus: string;
  uploadError: string | null;
  uploadResult: UploadResponse | null;
  onFileChange: (file: File | null) => void;
  onUpload: () => void;
};

export function UploadPanel({
  fileName,
  isUploading,
  uploadStatus,
  uploadError,
  uploadResult,
  onFileChange,
  onUpload,
}: UploadPanelProps) {
  const [isDragActive, setIsDragActive] = useState(false);

  const uploadSummary = uploadResult
    ? uploadResult.already_exists
      ? "复用已有索引"
      : "新建索引完成"
    : null;

  function isPdfFile(file: File): boolean {
    return file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
  }

  function hasDraggedFiles(event: DragEvent<HTMLLabelElement>): boolean {
    return Array.from(event.dataTransfer?.types ?? []).includes("Files");
  }

  function handleDragEnter(event: DragEvent<HTMLLabelElement>) {
    if (!hasDraggedFiles(event)) {
      return;
    }

    event.preventDefault();
    setIsDragActive(true);
  }

  function handleDragOver(event: DragEvent<HTMLLabelElement>) {
    if (!hasDraggedFiles(event)) {
      return;
    }

    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
    setIsDragActive(true);
  }

  function handleDragLeave(event: DragEvent<HTMLLabelElement>) {
    if (event.currentTarget.contains(event.relatedTarget as Node | null)) {
      return;
    }

    setIsDragActive(false);
  }

  function handleDrop(event: DragEvent<HTMLLabelElement>) {
    if (!hasDraggedFiles(event)) {
      return;
    }

    event.preventDefault();
    setIsDragActive(false);

    const droppedFile = event.dataTransfer.files?.[0] ?? null;
    onFileChange(droppedFile && isPdfFile(droppedFile) ? droppedFile : null);
  }

  return (
    <section className="self-start rounded-3xl border border-white/70 bg-white/90 p-6 shadow-xl shadow-slate-200/80 backdrop-blur">
      <div className="flex flex-col gap-4">
        <div className="space-y-1.5">
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-700">
            第一步
          </p>
          <h2 className="text-2xl font-semibold text-slate-950">上传 PDF</h2>
          <p className="text-sm leading-6 text-slate-600">
            选择文件并完成索引，随后就能在右侧连续提问。
          </p>
        </div>

        <label
          className={`flex cursor-pointer flex-col gap-2 rounded-2xl border border-dashed p-4 text-sm text-slate-600 transition ${
            isDragActive
              ? "border-sky-500 bg-sky-50 text-sky-700 shadow-[0_0_0_3px_rgba(14,165,233,0.12)]"
              : "border-slate-300 bg-slate-50 hover:border-sky-400 hover:bg-sky-50/60"
          }`}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <span className="font-medium text-slate-900">选择 PDF 文件</span>
          <span className={isDragActive ? "text-sky-700" : "text-slate-500"}>
            {isDragActive ? "松开鼠标以选中这个 PDF。" : "点击选择，或把 PDF 拖到这里。"}
          </span>
          <span className="truncate">{fileName || "还没有选择文件。"}</span>
          <input
            className="hidden"
            type="file"
            accept="application/pdf,.pdf"
            onChange={(event) => {
              onFileChange(event.target.files?.[0] ?? null);
            }}
          />
        </label>

        <div className="flex flex-wrap items-center gap-3">
          <button
            className="inline-flex min-w-28 items-center justify-center rounded-full bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
            disabled={!fileName || isUploading}
            onClick={onUpload}
            type="button"
          >
            {isUploading ? "处理中..." : "上传 PDF"}
          </button>
          <span aria-live="polite" className="text-sm text-slate-500">
            {uploadStatus}
          </span>
        </div>

        {uploadError ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {uploadError}
          </div>
        ) : null}

        {uploadResult ? (
          <div className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3">
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">索引状态</p>
                <p className="font-medium text-slate-900">{uploadSummary}</p>
              </div>
              <div className="rounded-full bg-sky-50 px-3 py-1 text-xs font-medium text-sky-700">
                {uploadResult.page_count} 页
              </div>
            </div>

            <div className="grid gap-x-4 gap-y-3 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">文件名</p>
                <p className="mt-1 break-all font-medium text-slate-900">{uploadResult.filename}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">document_id</p>
                <p className="mt-1 break-all font-mono text-[13px] text-slate-700">{uploadResult.document_id}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">分块</p>
                <p className="mt-1 font-medium text-slate-900">{uploadResult.chunk_count ?? "-"}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">新增分块</p>
                <p className="mt-1 font-medium text-slate-900">{uploadResult.indexed_new_chunks ?? "-"}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">文本长度</p>
                <p className="mt-1 font-medium text-slate-900">{uploadResult.text_length}</p>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
