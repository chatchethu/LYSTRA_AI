"use client";

import React from "react";
import ReactMarkdown from "react-markdown";

export interface UIBlock {
  id?: string;
  type: string;
  data?: any;
  metadata?: {
    priority?: "critical" | "high" | "normal" | "low";
    density?: "compact" | "comfortable";
    expandable?: boolean;
  };
}

export function BlockRenderer({ block }: { block: UIBlock }) {
  // Guard: if block itself is invalid, render nothing
  if (!block || typeof block !== "object") return null;

  // Support both nested { data: { ... } } and flat { text: "..." } schemas
  const data = { ...block, ...(block.data || {}) };

  const priorityStyles: Record<string, string> = {
    critical: "border-l-4 border-red-500 bg-red-500/10 p-3 rounded-r-lg",
    high: "border-l-4 border-primary bg-primary/10 p-3 rounded-r-lg",
    normal: "my-2",
    low: "opacity-75 text-sm",
  };

  const priorityClass =
    block.metadata?.priority
      ? priorityStyles[block.metadata.priority] ?? priorityStyles.normal
      : priorityStyles.normal;

  switch (block.type) {
    case "text":
      return (
        <div className={priorityClass}>
          <ReactMarkdown
            className="text-[15px] leading-[1.75] text-white/90 space-y-3"
            components={{
              p: ({ children }) => <p className="mb-3 last:mb-0 text-white/90 leading-relaxed">{children}</p>,
              strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
              em: ({ children }) => <em className="italic text-white/75">{children}</em>,
              ul: ({ children }) => <ul className="list-disc pl-5 space-y-1 my-2 text-white/85">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-5 space-y-1 my-2 text-white/85">{children}</ol>,
              li: ({ children }) => <li className="text-white/85 leading-relaxed">{children}</li>,
              code: ({ children }) => <code className="bg-white/10 rounded px-1.5 py-0.5 text-[0.85em] font-mono text-purple-300">{children}</code>,
              a: ({ href, children }) => {
                let safeHref = href || "#";
                if (safeHref.toLowerCase().startsWith("javascript:") || safeHref.toLowerCase().startsWith("data:")) {
                  safeHref = "#";
                }
                return <a href={safeHref} target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:text-purple-300 underline underline-offset-2">{children}</a>;
              },
            }}
          >
            {data.text || data.content || ""}
          </ReactMarkdown>
        </div>
      );

    case "heading": {
      const level = Math.min(Math.max(Number(data.level) || 2, 1), 6);
      const Tag = `h${level}` as keyof JSX.IntrinsicElements;
      const headingSizes: Record<number, string> = {
        1: "text-2xl font-bold text-white mt-6 mb-3",
        2: "text-xl font-semibold text-white mt-5 mb-2",
        3: "text-lg font-semibold text-white/90 mt-4 mb-2",
        4: "text-base font-semibold text-white/80 mt-3 mb-1",
        5: "text-sm font-semibold text-white/70 mt-2 mb-1",
        6: "text-sm font-medium text-white/60 mt-2 mb-1",
      };
      return <Tag className={headingSizes[level]}>{data.text || ""}</Tag>;
    }

    case "list": {
      const ListTag = data.style === "ordered" ? "ol" : "ul";
      const items: string[] = Array.isArray(data.items) ? data.items : [];
      return (
        <ListTag
          className={`pl-5 space-y-2 my-3 text-white/90 text-[15px] leading-relaxed ${
            data.style === "ordered" ? "list-decimal" : "list-disc"
          }`}
        >
          {items.map((item, i) => (
            <li key={i} className="text-white/90">{item}</li>
          ))}
        </ListTag>
      );
    }

    case "callout": {
      const colors: Record<string, string> = {
        warning: "bg-orange-500/10 border-orange-500/30 text-orange-200",
        info: "bg-blue-500/10 border-blue-500/30 text-blue-200",
        success: "bg-green-500/10 border-green-500/30 text-green-200",
        error: "bg-red-500/10 border-red-500/30 text-red-200",
        note: "bg-indigo-500/10 border-indigo-500/30 text-indigo-200",
      };
      const color =
        colors[data.intent as string] ?? colors.info;
      return (
        <div className={`p-4 rounded-xl border ${color} my-4 text-sm leading-relaxed`}>
          {data.text || data.message || ""}
        </div>
      );
    }

    case "table": {
      const columns: string[] = Array.isArray(data.columns) ? data.columns : [];
      const rows: string[][] = Array.isArray(data.rows) ? data.rows : [];
      if (columns.length === 0 && rows.length === 0) return null;
      return (
        <div className="w-full overflow-x-auto my-6 rounded-lg border border-white/[0.08] bg-black/20">
          <table className="w-full text-sm text-left">
            <thead className="bg-white/[0.04] text-white/70 uppercase text-[11px] tracking-wider">
              <tr>
                {columns.map((col, i) => (
                  <th key={i} className="px-4 py-3 font-medium border-b border-white/[0.08]">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {rows.map((row, i) => (
                <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                  {(Array.isArray(row) ? row : []).map((cell, j) => (
                    <td key={j} className="px-4 py-3 text-white/80 whitespace-pre-wrap">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    case "code":
      return (
        <div className="my-4 rounded-xl overflow-hidden border border-white/[0.08] bg-[#0d0d0d]">
          <div className="bg-black/40 px-4 py-2 border-b border-white/[0.08] text-xs font-mono text-white/40 flex justify-between">
            <span>{data.language || "code"}</span>
          </div>
          <div className="p-4 overflow-x-auto custom-scrollbar">
            <pre className="text-sm font-mono text-blue-300">
              <code>{data.code || data.content || ""}</code>
            </pre>
          </div>
        </div>
      );

    default:
      // Safe fallback — show a subtle debug card instead of crashing
      return (
        <div className="p-3 my-2 border border-white/10 bg-white/5 rounded-lg text-xs font-mono text-white/50 overflow-auto">
          {JSON.stringify(block, null, 2)}
        </div>
      );
  }
}
