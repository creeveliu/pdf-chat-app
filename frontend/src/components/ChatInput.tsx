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
    <section className="rounded-[1.75rem] border border-slate-200 bg-slate-100 p-4 text-slate-900 shadow-lg shadow-slate-300/25">
      <div className="flex flex-col gap-3">
        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-700">输入你的问题</span>
          <textarea
            className="min-h-24 w-full rounded-[1.35rem] border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-900 outline-none placeholder:text-slate-400 focus:border-sky-400"
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
            <p className="text-sm text-slate-600">{statusText}</p>
            {errorText ? <p className="text-sm text-rose-600">{errorText}</p> : null}
          </div>

          <button
            className="inline-flex min-w-32 items-center justify-center rounded-full bg-slate-800 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500"
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
