type QuestionPanelProps = {
  question: string;
  topK: number;
  canAsk: boolean;
  isAsking: boolean;
  askStatus: string;
  askError: string | null;
  onQuestionChange: (value: string) => void;
  onTopKChange: (value: number) => void;
  onAsk: () => void;
};

export function QuestionPanel({
  question,
  topK,
  canAsk,
  isAsking,
  askStatus,
  askError,
  onQuestionChange,
  onTopKChange,
  onAsk,
}: QuestionPanelProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-slate-950 p-8 text-slate-50 shadow-xl shadow-slate-300/40">
      <div className="flex flex-col gap-6">
        <div className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-300">
            第二步
          </p>
          <h2 className="text-2xl font-semibold">输入问题</h2>
          <p className="text-sm leading-6 text-slate-300">
            系统会使用已建立索引的 PDF 内容作为上下文。如果后端还没有索引，会明确返回错误信息。
          </p>
        </div>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-200">问题</span>
          <textarea
            className="min-h-32 w-full rounded-2xl border border-white/15 bg-white/5 px-4 py-3 text-sm text-white outline-none ring-0 placeholder:text-slate-400 focus:border-sky-400"
            placeholder="这份 PDF 主要讲了什么？"
            value={question}
            onChange={(event) => {
              onQuestionChange(event.target.value);
            }}
          />
        </label>

        <div className="flex flex-wrap items-end gap-4">
          <label className="max-w-56 space-y-2">
            <span className="text-sm font-medium text-slate-200">参考片段数量</span>
            <p className="text-xs leading-5 text-slate-400">
              回答前先从 PDF 中取多少段最相关内容作为参考。默认 3 段，通常已经够用。
            </p>
            <input
              className="w-24 rounded-2xl border border-white/15 bg-white/5 px-4 py-3 text-sm text-white outline-none focus:border-sky-400"
              max={10}
              min={1}
              type="number"
              value={topK}
              onChange={(event) => {
                onTopKChange(Number(event.target.value));
              }}
            />
          </label>

          <button
            className="inline-flex min-w-32 items-center justify-center rounded-full bg-sky-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:bg-slate-500 disabled:text-slate-300"
            disabled={!canAsk || !question.trim() || isAsking}
            onClick={onAsk}
            type="button"
          >
            {isAsking ? "提问中..." : "开始提问"}
          </button>

          <span className="text-sm text-slate-400">{askStatus}</span>
        </div>

        {askError ? (
          <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {askError}
          </div>
        ) : null}
      </div>
    </section>
  );
}
