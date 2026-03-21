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
  return (
    <section className="rounded-3xl border border-white/70 bg-white/90 p-8 shadow-xl shadow-slate-200/80 backdrop-blur">
      <div className="flex flex-col gap-6">
        <div className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-700">
            第一步
          </p>
          <h2 className="text-2xl font-semibold text-slate-950">上传 PDF</h2>
          <p className="text-sm leading-6 text-slate-600">
            选择一个 PDF，发送到后端，并等待解析与索引建立完成。
          </p>
        </div>

        <label className="flex cursor-pointer flex-col gap-3 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-600 transition hover:border-sky-400 hover:bg-sky-50/60">
          <span className="font-medium text-slate-900">选择 PDF 文件</span>
          <span>{fileName || "还没有选择文件。"}</span>
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
            className="inline-flex min-w-32 items-center justify-center rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
            disabled={!fileName || isUploading}
            onClick={onUpload}
            type="button"
          >
            {isUploading ? "上传中..." : "上传 PDF"}
          </button>
          <span className="text-sm text-slate-500">{uploadStatus}</span>
        </div>

        {uploadError ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {uploadError}
          </div>
        ) : null}

        {uploadResult ? (
          <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-5 text-sm text-slate-700">
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">索引状态</p>
              <p className="mt-1 font-medium text-slate-900">
                {uploadResult.already_exists
                  ? "检测到重复文档，已复用已有索引。"
                  : "已完成新文档解析与索引建立。"}
              </p>
              <p className="mt-2 text-xs leading-5 text-slate-500">
                document_id: <span className="font-mono text-slate-700">{uploadResult.document_id}</span>
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">文件名</p>
              <p className="mt-1 font-medium text-slate-900">{uploadResult.filename}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">页数</p>
              <p className="mt-1 font-medium text-slate-900">{uploadResult.page_count}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">文本长度</p>
              <p className="mt-1 font-medium text-slate-900">{uploadResult.text_length}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">分块数量</p>
              <p className="mt-1 font-medium text-slate-900">{uploadResult.chunk_count ?? "-"}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">新增分块</p>
              <p className="mt-1 font-medium text-slate-900">{uploadResult.indexed_new_chunks ?? "-"}</p>
            </div>
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
