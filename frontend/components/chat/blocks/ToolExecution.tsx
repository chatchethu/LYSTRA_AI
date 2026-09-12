import React from "react";
import { Loader2, CheckCircle2, ChevronRight } from "lucide-react";
import clsx from "clsx";

export function AgentStatus({ status }: { status: string }) {
  if (!status) return null;
  return (
    <div className="flex items-center gap-2 text-xs font-medium text-text-secondary animate-pulse px-2 py-1 bg-white/5 w-fit rounded-full border border-white/5">
      <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
      {status}...
    </div>
  );
}

export function ToolExecution({ name, status, result_summary }: { name: string; status: string; result_summary?: string }) {
  const isComplete = status === "complete" || status === "success";
  const isFailed = status === "error" || status === "failed";
  
  return (
    <div className={clsx(
      "flex flex-col gap-1.5 p-3 rounded-lg border text-sm max-w-sm transition-colors",
      isComplete ? "bg-surface border-success/20" : isFailed ? "bg-error/10 border-error/20" : "bg-surface border-border"
    )}>
      <div className="flex items-center gap-2">
        {isComplete ? (
          <CheckCircle2 className="w-4 h-4 text-success" />
        ) : isFailed ? (
          <div className="w-2 h-2 rounded-full bg-error" />
        ) : (
          <Loader2 className="w-4 h-4 animate-spin text-accent" />
        )}
        <span className={clsx("font-medium", isFailed ? "text-error" : "text-text-primary")}>
          {isComplete ? `${name} complete` : `Running ${name}...`}
        </span>
      </div>
      {isComplete && result_summary && (
        <div className="flex items-start gap-1.5 mt-1 text-xs text-text-muted pl-6">
          <ChevronRight className="w-3.5 h-3.5 shrink-0 mt-0.5 text-success/50" />
          <span className="truncate">{result_summary}</span>
        </div>
      )}
    </div>
  );
}
