"use client";

import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";


type ChatMarkdownProps = {
  content: string;
};

const markdownComponents: Components = {
  a: ({ node, className, ...props }) => {
    void node;

    return (
      <a
        {...props}
        className={["font-medium text-sky-700 underline underline-offset-4 break-all", className]
          .filter(Boolean)
          .join(" ")}
        rel="noreferrer"
        target="_blank"
      />
    );
  },
};

const markdownClassName = [
  "mt-2 break-words text-sm leading-7 text-slate-800",
  "[&_h1]:mt-5 [&_h1:first-child]:mt-0 [&_h1]:text-2xl [&_h1]:font-semibold [&_h1]:tracking-tight",
  "[&_h2]:mt-5 [&_h2:first-child]:mt-0 [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:tracking-tight",
  "[&_h3]:mt-4 [&_h3:first-child]:mt-0 [&_h3]:text-base [&_h3]:font-semibold",
  "[&_p]:my-3 [&_p:first-child]:mt-0 [&_p:last-child]:mb-0",
  "[&_ul]:my-3 [&_ul]:list-disc [&_ul]:pl-6",
  "[&_ol]:my-3 [&_ol]:list-decimal [&_ol]:pl-6",
  "[&_li]:my-1.5",
  "[&_blockquote]:my-4 [&_blockquote]:border-l-4 [&_blockquote]:border-sky-200 [&_blockquote]:bg-sky-50/80 [&_blockquote]:px-4 [&_blockquote]:py-2 [&_blockquote]:text-slate-700",
  "[&_hr]:my-4 [&_hr]:border-0 [&_hr]:border-t [&_hr]:border-slate-200",
  "[&_pre]:my-4 [&_pre]:overflow-x-auto [&_pre]:rounded-2xl [&_pre]:border [&_pre]:border-slate-200 [&_pre]:bg-slate-950 [&_pre]:p-4 [&_pre]:text-[13px] [&_pre]:leading-6 [&_pre]:text-slate-100",
  "[&_code]:rounded [&_code]:bg-slate-200/80 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-[0.9em]",
  "[&_pre_code]:bg-transparent [&_pre_code]:p-0 [&_pre_code]:text-inherit",
  "[&_a:hover]:text-sky-800",
  "[&_table]:my-4 [&_table]:w-full [&_table]:border-collapse [&_table]:overflow-hidden [&_table]:rounded-2xl",
  "[&_thead]:bg-slate-100",
  "[&_th]:border [&_th]:border-slate-200 [&_th]:px-3 [&_th]:py-2 [&_th]:text-left [&_th]:font-semibold",
  "[&_td]:border [&_td]:border-slate-200 [&_td]:px-3 [&_td]:py-2",
].join(" ");

export function ChatMarkdown({ content }: ChatMarkdownProps) {
  return (
    <div className={markdownClassName}>
      <ReactMarkdown components={markdownComponents} remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
