import React, { memo, useState, useCallback } from "react";
import { MessageSquareReply, RefreshCcw, ThumbsUp, ThumbsDown } from "lucide-react";
import { CopyButton } from "@/components/ui/CopyButton";

interface MessageActionsProps {
  content: string;
  onRegenerate?: () => void;
  onReply?: () => void;
  onFeedback?: (vote: "up" | "down") => void;
}

export const MessageActions = memo(function MessageActions({ content, onRegenerate, onReply, onFeedback }: MessageActionsProps) {
  const [vote, setVote] = useState<"up" | "down" | null>(null);

  const handleVote = useCallback(
    (next: "up" | "down") => {
      setVote((prev) => (prev === next ? null : next));
      onFeedback?.(next);
    },
    [onFeedback]
  );

  return (
    <div className="flex items-center gap-1 mt-1 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity -ml-1.5">
      {onReply && (
        <button
          type="button"
          onClick={onReply}
          aria-label="Reply to message"
          className="p-1.5 text-text-muted hover:text-text-primary hover:bg-white/5 rounded-md transition-colors"
          title="Reply"
        >
          <MessageSquareReply className="w-3.5 h-3.5" aria-hidden="true" />
        </button>
      )}
      <CopyButton text={content} />
      {onRegenerate && (
        <button
          type="button"
          onClick={onRegenerate}
          aria-label="Regenerate response"
          className="p-1.5 text-text-muted hover:text-text-primary hover:bg-white/5 rounded-md transition-colors"
          title="Regenerate"
        >
          <RefreshCcw className="w-3.5 h-3.5" aria-hidden="true" />
        </button>
      )}
      <div className="w-px h-3 bg-border mx-1" />
      <button
        type="button"
        onClick={() => handleVote("up")}
        aria-pressed={vote === "up"}
        aria-label="Good response"
        className={`p-1.5 rounded-md transition-colors ${vote === "up" ? "text-success bg-success/10" : "text-text-muted hover:text-success hover:bg-success/10"}`}
        title="Good response"
      >
        <ThumbsUp className="w-3.5 h-3.5" aria-hidden="true" />
      </button>
      <button
        type="button"
        onClick={() => handleVote("down")}
        aria-pressed={vote === "down"}
        aria-label="Bad response"
        className={`p-1.5 rounded-md transition-colors ${vote === "down" ? "text-error bg-error/10" : "text-text-muted hover:text-error hover:bg-error/10"}`}
        title="Bad response"
      >
        <ThumbsDown className="w-3.5 h-3.5" aria-hidden="true" />
      </button>
    </div>
  );
});
