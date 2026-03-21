import type { AskContext } from "@/lib/api";

type AnswerPanelProps = {
  answer: string | null;
  contexts: AskContext[];
};

export function AnswerPanel({ answer, contexts }: AnswerPanelProps) {
  return (
    <section className="rounded-3xl border border-white/70 bg-white/90 p-8 shadow-xl shadow-slate-200/80 backdrop-blur">
      <div className="flex flex-col gap-6">
        <div className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-700">
            第三步
          </p>
          <h2 className="text-2xl font-semibold text-slate-950">回答与引用片段</h2>
          <p className="text-sm leading-6 text-slate-600">
            这里会展示基于 PDF 上下文生成的回答，以及命中的引用片段。
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">回答</p>
          <div className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">
            {answer ?? "上传 PDF 并提问后，回答会显示在这里。"}
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">引用片段</p>
          {contexts.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-sm text-slate-500">
              暂时还没有引用片段。
            </div>
          ) : (
            contexts.map((context) => (
              <article
                key={`${context.document_id}-${context.chunk_id}`}
                className="rounded-2xl border border-slate-200 bg-slate-50 p-5"
              >
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs uppercase tracking-[0.16em] text-slate-400">
                  <span>{context.filename}</span>
                  <span>片段 #{context.chunk_id}</span>
                  <span>分数 {context.score.toFixed(3)}</span>
                </div>
                <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">
                  {context.text}
                </p>
              </article>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
