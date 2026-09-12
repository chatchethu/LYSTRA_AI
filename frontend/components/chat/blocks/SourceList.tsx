import React, { memo } from "react";
import { Link2 } from "lucide-react";

export interface SourceItemData {
  title: string;
  url?: string;
  domain?: string;
  snippet?: string;
}

export const SourceItem = memo(function SourceItem({ src }: { src: SourceItemData }) {
  const domain = src.domain || (src.url ? new URL(src.url).hostname : "Internal");
  return (
    <a 
      href={src.url || "#"} 
      target="_blank" 
      rel="noreferrer"
      className="flex flex-col gap-0.5 p-2.5 rounded-lg bg-surface border border-border hover:border-primary/40 hover:bg-white/[0.04] transition-all group"
    >
      <span className="text-sm font-medium text-text-primary group-hover:text-primary transition-colors truncate">
        {src.title}
      </span>
      <span className="text-xs text-text-muted truncate">
        {domain}
      </span>
    </a>
  );
});

export const SourceList = memo(function SourceList({ sources }: { sources: SourceItemData[] }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="flex flex-col gap-2 mt-2 w-full max-w-sm">
      <div className="text-xs font-semibold uppercase tracking-widest text-text-muted mb-1 flex items-center gap-1.5">
        <Link2 className="w-3.5 h-3.5" />
        Sources
      </div>
      <div className="flex flex-col gap-1.5">
        {sources.map((src, i) => (
          <SourceItem key={i} src={src} />
        ))}
      </div>
    </div>
  );
});
