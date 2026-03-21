"use client";

type ChatInputProps = {
  question: string;
  isSending: boolean;
  isDisabled: boolean;
  statusText: string;
  errorText: string | null;
  onQuestionChange: (value: string) => void;
  onSend: () => void;
};

export function ChatInput({
  question,
  isSending,
  isDisabled,
  statusText,
  errorText,
  onQuestionChange,
  onSend,
}: ChatInputProps) {
  return (
    <section className="rounded-[2rem] border border-slate-200 bg-slate-950 p-5 text-white shadow-xl shadow-slate-300/40">
      <div className="flex flex-col gap-4">
        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-200">输入你的问题</span>
          <textarea
            className="min-h-28 w-full rounded-[1.5rem] border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-400 focus:border-sky-400"
            disabled={isDisabled || isSending}
            placeholder={isDisabled ? "请先上传并完成索引一个 PDF。" : "例如：这份说明书主要讲了什么？"}
            value={question}
            onChange={(event) => {
              onQuestionChange(event.target.value);
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                onSend();
              }
            }}
          />
        </label>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <p className="text-sm text-slate-300">{statusText}</p>
            {errorText ? <p className="text-sm text-rose-300">{errorText}</p> : null}
          </div>

          <button
            className="inline-flex min-w-32 items-center justify-center rounded-full bg-sky-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:bg-slate-600 disabled:text-slate-300"
            disabled={isDisabled || isSending || !question.trim()}
            onClick={onSend}
            type="button"
          >
            {isSending ? "发送中..." : "发送问题"}
          </button>
        </div>
      </div>
    </section>
  );
}
