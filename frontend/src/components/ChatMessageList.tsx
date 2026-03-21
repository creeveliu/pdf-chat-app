"use client";

import { useEffect, useRef } from "react";

import { AnswerCitations } from "@/components/AnswerCitations";
import type { ChatMessage } from "@/types/chat";


function formatTimeLabel(isoDateTime: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(isoDateTime));
}

type ChatMessageListProps = {
  messages: ChatMessage[];
  isAsking: boolean;
};

export function ChatMessageList({ messages, isAsking }: ChatMessageListProps) {
  const scrollRegionRef = useRef<HTMLDivElement | null>(null);
  const shouldAutoScrollRef = useRef(true);
  const previousIsAskingRef = useRef(isAsking);
  const shouldIgnoreNextScrollEventRef = useRef(false);
  const hasStreamingAssistant = messages.some(
    (message) => message.role === "assistant" && message.isStreaming,
  );

  function isNearBottom(element: HTMLDivElement): boolean {
    const distanceFromBottom = element.scrollHeight - element.scrollTop - element.clientHeight;
    return distanceFromBottom <= 80;
  }

  useEffect(() => {
    if (!previousIsAskingRef.current && isAsking) {
      shouldAutoScrollRef.current = true;
    }

    previousIsAskingRef.current = isAsking;
  }, [isAsking]);

  useEffect(() => {
    const scrollRegion = scrollRegionRef.current;
    if (!scrollRegion || !shouldAutoScrollRef.current) {
      return;
    }

    shouldIgnoreNextScrollEventRef.current = true;

    if (typeof scrollRegion.scrollTo === "function") {
      scrollRegion.scrollTo({
        top: scrollRegion.scrollHeight,
        behavior: "auto",
      });
      return;
    }
    scrollRegion.scrollTop = scrollRegion.scrollHeight;
  }, [isAsking, messages]);

  return (
    <section className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-[2rem] border border-white/80 bg-white/92 shadow-2xl shadow-slate-200/70 backdrop-blur">
      <div className="border-b border-slate-200/80 px-6 py-4">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">聊天区</p>
        <h2 className="mt-2 text-xl font-semibold text-slate-950">围绕当前 PDF 连续提问</h2>
      </div>

      <div
        ref={scrollRegionRef}
        className="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-6"
        onScroll={(event) => {
          if (shouldIgnoreNextScrollEventRef.current) {
            shouldIgnoreNextScrollEventRef.current = false;
            return;
          }

          shouldAutoScrollRef.current = isNearBottom(event.currentTarget);
        }}
      >
        {messages.map((message) => {
          if (message.role === "system") {
            const toneStyles =
              message.tone === "error"
                ? "border-rose-200 bg-rose-50 text-rose-700"
                : message.tone === "success"
                  ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                  : "border-slate-200 bg-slate-100 text-slate-600";

            return (
              <div key={message.id} className="flex justify-center">
                <div className={`max-w-2xl rounded-full border px-4 py-2 text-sm ${toneStyles}`}>
                  {message.content}
                </div>
              </div>
            );
          }

          if (message.role === "user") {
            return (
              <div key={message.id} className="flex justify-end">
                <article className="max-w-3xl rounded-[1.75rem] rounded-br-md border border-slate-200 bg-slate-200 px-5 py-4 text-sm leading-7 text-slate-900 shadow-sm">
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">你</p>
                  <p className="mt-2 whitespace-pre-wrap">{message.content}</p>
                  <p className="mt-3 text-right text-xs text-slate-500">{formatTimeLabel(message.createdAt)}</p>
                </article>
              </div>
            );
          }

          return (
            <div key={message.id} className="flex justify-start">
              <article className="max-w-4xl rounded-[1.75rem] rounded-bl-md border border-slate-200 bg-slate-50 px-5 py-4 text-sm leading-7 text-slate-800 shadow-sm">
                <div className="flex items-center gap-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-sky-700">AI</p>
                  {message.isStreaming ? (
                    <span className="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-[11px] font-medium text-sky-700">
                      <span className="h-2 w-2 animate-pulse rounded-full bg-sky-500" />
                      生成中
                    </span>
                  ) : null}
                </div>
                <p className="mt-2 whitespace-pre-wrap">{message.content}</p>
                <AnswerCitations citations={message.citations} contexts={message.contexts} />
                <p className="mt-3 text-right text-xs text-slate-400">{formatTimeLabel(message.createdAt)}</p>
              </article>
            </div>
          );
        })}

        {isAsking && !hasStreamingAssistant ? (
          <div className="flex justify-start">
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
              <span className="h-2 w-2 animate-pulse rounded-full bg-sky-400" />
              正在生成回答...
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
