import React from "react";
import { Brain, Sparkles } from "lucide-react";
import { useChatStore } from "@/store/chatStore";

export function ChatHeader() {
  const isGenerating = useChatStore(state => state.isGenerating);
  const streamingStatus = useChatStore(state => state.streamingStatus);
  const activeTask = useChatStore(state => state.activeTask);

  let statusText = "Ready";
  if (streamingStatus === "reconnecting") statusText = "Reconnecting...";
  else if (isGenerating) statusText = "Thinking...";

  return (
    <div className="relative top-0 left-0 w-full bg-background/80 backdrop-blur-md border-b border-border z-30 px-4 py-3 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-3">
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="font-heading font-bold text-sm tracking-tight text-text-primary">LYSTRA</span>
            {activeTask && (
              <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-[10px] uppercase font-semibold tracking-wider text-text-muted flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-primary" />
                Task Active
              </span>
            )}
          </div>
          <span className="text-xs text-text-muted flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${isGenerating ? "bg-primary animate-pulse" : "bg-success"}`} />
            {statusText}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-[10px] text-text-muted uppercase tracking-wider hidden sm:block">Powered by LYSTRA</span>
      </div>
    </div>
  );
}
