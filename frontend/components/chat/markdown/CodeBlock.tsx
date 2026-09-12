import React, { memo } from "react";
import dynamic from "next/dynamic";
import { CopyButton } from "@/components/ui/CopyButton";

// FE-91: Dynamically import SyntaxHighlighter to avoid blocking the main thread during initial load
const SyntaxHighlighter = dynamic(
  () => import("react-syntax-highlighter").then((mod) => mod.Prism),
  { ssr: false, loading: () => <div className="p-4 text-xs text-text-muted">Loading code editor...</div> }
);

import { vscDarkPlus } from "react-syntax-highlighter/dist/cjs/styles/prism";

interface CodeBlockProps {
  language: string;
  value: string;
}

export const CodeBlock = memo(function CodeBlock({ language, value }: CodeBlockProps) {
  return (
    <div className="my-4 rounded-lg overflow-hidden border border-border bg-[#0d1117]">
      <div className="flex items-center justify-between px-4 py-1.5 bg-white/5 border-b border-border">
        <span className="text-xs font-mono text-text-muted capitalize">
          {language || "text"}
        </span>
        <CopyButton text={value} />
      </div>
      <div className="p-0 text-[13px] custom-scrollbar overflow-x-auto">
        <SyntaxHighlighter
          language={language || "text"}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            padding: "1rem",
            background: "transparent",
            fontSize: "inherit"
          }}
          codeTagProps={{
            style: { fontFamily: "var(--font-roboto-mono), monospace" }
          }}
        >
          {value}
        </SyntaxHighlighter>
      </div>
    </div>
  );
});
