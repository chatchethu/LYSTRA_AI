import React, { memo, useMemo, useCallback } from "react";
import { MessageStatus, NovaBlock } from "@/store/chatStore";
import { ResponseRenderer } from "./markdown/ResponseRenderer";
import { BlocksRenderer } from "./blocks/BlocksRenderer";
import { MessageActions } from "./MessageActions";

interface AssistantMessageProps {
  content: string;
  blocks?: NovaBlock[];
  status: MessageStatus;
  isThinking?: boolean;
  isGroupStart?: boolean;
  isGroupEnd?: boolean;
  onRegenerate?: () => void;
  onReply?: () => void;
  onFeedback?: (vote: "up" | "down") => void;
}

const TEXT_BLOCK_TYPES = new Set(["text", "markdown"]);

function useNormalizedMessage(content: string, blocks: NovaBlock[] | undefined) {
  return useMemo(() => {
    const fallbackBlocks = blocks ?? [];
    const trimmed = typeof content === "string" ? content.trim() : "";

    // Only attempt JSON parse if the content is strictly a JSON array of objects.
    // "[{" + "}]" is the canonical shape of a NovaBlock array from the backend.
    // This permanently prevents false-positive parse attempts on:
    //  - Markdown numbered lists:  "[1] First item..."
    //  - LLM error strings:        "[Error: could not prepare response.]"
    //  - Markdown reference links: "[link text](url)"
    //  - Any other plain text beginning with "["
    if (!trimmed.startsWith("[{") || !trimmed.endsWith("}]")) {
      return { displayContent: content, displayBlocks: fallbackBlocks };
    }

    try {
      const parsed = JSON.parse(trimmed);
      if (!Array.isArray(parsed)) {
        return { displayContent: content, displayBlocks: fallbackBlocks };
      }

      const textBlock = parsed.find((b) => TEXT_BLOCK_TYPES.has(b?.type));
      return {
        displayContent: textBlock?.text ?? textBlock?.content ?? textBlock?.data ?? "",
        displayBlocks: parsed as NovaBlock[],
      };
    } catch {
      // Passed the heuristic but still invalid JSON — silently treat as plain markdown.
      return { displayContent: content, displayBlocks: fallbackBlocks };
    }
  }, [content, blocks]);
}

// removed Brain import

export const AssistantMessage = memo(function AssistantMessage({
  content,
  blocks,
  status,
  isThinking,
  isGroupStart,
  isGroupEnd,
  onRegenerate,
  onReply,
  onFeedback,
}: AssistantMessageProps) {
  const { displayContent, displayBlocks } = useNormalizedMessage(content, blocks);

  const nonTextBlocks = useMemo(
    () => displayBlocks.filter((b) => !TEXT_BLOCK_TYPES.has(b.type)),
    [displayBlocks]
  );

  const isStreaming = status === "streaming" || status === "pending";

  return (
    <div className="w-full flex group pl-4">
      <div className="flex-1 flex flex-col gap-3 min-w-0 py-4 border-transparent">
        {isThinking && (
          <div
            role="status"
            aria-live="polite"
            className="flex items-center gap-2 text-text-secondary text-sm font-medium animate-pulse"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "0ms" }} />
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "150ms" }} />
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "300ms" }} />
            <span className="ml-2">Thinking...</span>
          </div>
        )}

        {/* Phase RL-18: Canonical Response Renderer */}
        {(displayContent || isStreaming) && (
          <div className="min-w-0 w-full relative [&>*:first-child]:mt-0">
            <ResponseRenderer content={displayContent} isStreaming={isStreaming && !isThinking} />
          </div>
        )}

        {/* Handles Phase RL-19 Sources, Plans, Tools */}
        {nonTextBlocks.length > 0 && <BlocksRenderer blocks={nonTextBlocks} />}

        {/* Status / Failures */}
        {status === "failed" && (
          <div className="flex flex-col gap-2 mt-1">
            <div
              role="alert"
              className="text-error text-sm font-medium bg-error/10 border border-error/20 px-3 py-2 rounded-lg w-fit flex items-center gap-2"
            >
              <span>Something went wrong.</span>
            </div>
            {onRegenerate && (
              <button
                type="button"
                onClick={onRegenerate}
                className="w-fit text-xs font-semibold px-3 py-1.5 bg-surface border border-border rounded-md hover:bg-white/5 transition-colors text-text-secondary hover:text-text-primary flex items-center gap-1.5"
              >
                Try again
              </button>
            )}
          </div>
        )}

        {status === "cancelled" && (
          <div className="flex flex-col gap-2 mt-1">
            <div className="text-text-muted text-sm font-medium bg-surface border border-border px-3 py-2 rounded-lg w-fit flex items-center gap-2">
              <span>Generation stopped.</span>
            </div>
            {onRegenerate && (
              <button
                type="button"
                onClick={onRegenerate}
                className="w-fit text-xs font-semibold px-3 py-1.5 bg-surface border border-border rounded-md hover:bg-white/5 transition-colors text-text-secondary hover:text-text-primary flex items-center gap-1.5"
              >
                Regenerate
              </button>
            )}
          </div>
        )}

        {/* Phase RL-19: Message Actions */}
        {status === "completed" && (
          <MessageActions 
            content={displayContent} 
            onRegenerate={onRegenerate} 
            onReply={onReply}
            onFeedback={onFeedback} 
          />
        )}
      </div>
    </div>
  );
});
