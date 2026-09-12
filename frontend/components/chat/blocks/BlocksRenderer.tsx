import React, { memo } from "react";
import { NovaBlock } from "@/store/chatStore";
import { SourceList } from "./SourceList";
import { AgentStatus, ToolExecution } from "./ToolExecution";
import { PlanUI } from "./PlanUI";
import { ApprovalUI } from "./ApprovalUI";
import { MediaBlock } from "./MediaBlock";

interface BlocksRendererProps {
  blocks: NovaBlock[];
}

export const BlocksRenderer = memo(function BlocksRenderer({ blocks }: BlocksRendererProps) {
  if (!blocks || blocks.length === 0) return null;

  return (
    <div className="flex flex-col gap-3 mt-2 w-full">
      {blocks.map((block, idx) => {
        // Skip text/markdown blocks as they are handled by the main MarkdownRenderer
        if (block.type === "text" || block.type === "markdown") return null;
        const blockData: any = "data" in block ? block.data : block;

        switch (block.type) {
          case "image":
          case "file":
            return (
              <MediaBlock
                key={idx}
                type={blockData?.fileType || block.type}
                url={blockData?.url}
                name={blockData?.name}
                size={blockData?.size}
              />
            );
          case "approval":
            return (
              <ApprovalUI
                key={idx}
                action={blockData?.action || "Unknown action"}
                reason={blockData?.reason || "No reason provided"}
                status={blockData?.status || "pending"}
              />
            );
          case "sources":
            return <SourceList key={idx} sources={blockData?.items || []} />;
          case "status":
            return <AgentStatus key={idx} status={blockData?.text || ""} />;
          case "tool":
            return (
              <ToolExecution
                key={idx}
                name={blockData?.name || "Tool"}
                status={blockData?.status || "running"}
                result_summary={blockData?.result_summary}
              />
            );
          case "plan":
            return <PlanUI key={idx} steps={blockData?.steps || []} />;
          default:
            // Fallback for unknown blocks (for debug, optionally hide in production)
            return (
              <div key={idx} className="p-3 rounded-lg bg-surface border border-border text-sm max-w-md hidden">
                <div className="text-text-secondary font-mono text-xs uppercase mb-2 tracking-wider">{block.type}</div>
                <pre className="overflow-x-auto p-2 bg-background rounded custom-scrollbar text-text-primary text-[10px]">
                  <code>{JSON.stringify(blockData, null, 2)}</code>
                </pre>
              </div>
            );
        }
      })}
    </div>
  );
});
