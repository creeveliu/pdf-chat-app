"use client";

import { useState } from "react";

import type { AskContext, Citation } from "@/lib/api";


function formatPageLabel(pageNumbers: number[] | undefined, pageNumber?: number | null): string {
  if (pageNumbers && pageNumbers.length > 0) {
    return `第 ${pageNumbers.join("、")} 页`;
  }

  if (pageNumber) {
    return `第 ${pageNumber} 页`;
  }

  return "页码未知";
}

function buildCitationSummary(citations: Citation[]): string {
  const pageLabels = citations.map((citation) => formatPageLabel(citation.page_numbers, citation.page_number));
  const uniquePageLabels = Array.from(new Set(pageLabels));

  return `引用：${uniquePageLabels.join("、")}`;
}

type AnswerCitationsProps = {
  citations: Citation[];
  contexts: AskContext[];
};

export function AnswerCitations({ citations, contexts }: AnswerCitationsProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (citations.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm font-medium text-slate-700">{buildCitationSummary(citations)}</p>
        <button
          className="inline-flex items-center rounded-full border border-slate-300 px-3 py-1 text-xs font-medium text-slate-700 transition hover:border-sky-300 hover:bg-sky-50 hover:text-sky-700"
          onClick={() => {
            setIsOpen((currentValue) => !currentValue);
          }}
          type="button"
        >
          {isOpen ? "收起引用片段" : "查看引用片段"}
        </button>
      </div>

      {isOpen ? (
        <div className="mt-4 space-y-3">
          {contexts.map((context) => (
            <article
              key={`${context.document_id}-${context.chunk_id}`}
              className="rounded-2xl border border-slate-200 bg-white p-4"
            >
              <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-xs uppercase tracking-[0.14em] text-slate-400">
                <span>{context.filename}</span>
                <span>{formatPageLabel(context.page_numbers, context.page_number)}</span>
                <span>片段 #{context.chunk_index ?? context.chunk_id}</span>
              </div>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">{context.text}</p>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
}
