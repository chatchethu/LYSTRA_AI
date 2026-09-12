$code = @"
"use client";

import { useChatStore } from "@/store/chatStore";
import { UserMessage } from "./UserMessage";
import { AssistantMessage } from "./AssistantMessage";
import { useEffect, useRef, useState, useMemo } from "react";
import { ArrowDown } from "lucide-react";
import { motion } from "framer-motion";

export function MessageList() {
  const messages = useChatStore(state => state.messages);
  const streamingStatus = useChatStore(state => state.streamingStatus);
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  
  const [isAutoScrollPaused, setIsAutoScrollPaused] = useState(false);
  const [visibleCount, setVisibleCount] = useState(50); // Phase 31: Virtualization/Lazy Loading
  const setRegenerateMessageId = useChatStore(state => state.setRegenerateMessageId);

  const handleScroll = () => {
    if (!scrollContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    
    // Lazy load older messages when scrolling up
    if (scrollTop < 200 && visibleCount < messages.length) {
      setVisibleCount(prev => Math.min(prev + 50, messages.length));
    }

    const distanceToBottom = scrollHeight - scrollTop - clientHeight;
    setIsAutoScrollPaused(distanceToBottom > 50);
  };

  useEffect(() => {
    if (!isAutoScrollPaused) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isAutoScrollPaused]);

  const jumpToBottom = () => {
    setIsAutoScrollPaused(false);
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Phase 7 & 31: Grouping + Slice for Performance
  const groupedMessages = useMemo(() => {
    const sliced = messages.slice(Math.max(0, messages.length - visibleCount));
    return sliced.map((msg, index) => {
      const prevMsg = sliced[index - 1];
      const nextMsg = sliced[index + 1];
      
      const isGroupStart = !prevMsg || prevMsg.role !== msg.role;
      const isGroupEnd = !nextMsg || nextMsg.role !== msg.role;
      
      return { ...msg, isGroupStart, isGroupEnd };
    });
  }, [messages, visibleCount]);

  return (
    <div 
      ref={scrollContainerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto w-full custom-scrollbar pt-8 pb-32 relative"
    >
      <div className="max-w-3xl mx-auto px-4 flex flex-col gap-2"> 
        {visibleCount < messages.length && (
          <div className="text-center py-4 text-[var(--text-tertiary)] text-xs">
            Loading previous messages...
          </div>
        )}
        {groupedMessages.map((msg, i) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, ease: "easeOut" }} 
            style={{ 
              contentVisibility: "auto", 
              containIntrinsicSize: "0 100px",
              marginTop: msg.isGroupStart && i !== 0 ? "1.5rem" : "0" 
            }}
          >
            {msg.role === "user" ? (
              <UserMessage 
                content={msg.content} 
                status={msg.status} 
                isGroupStart={msg.isGroupStart}
                isGroupEnd={msg.isGroupEnd}
              />
            ) : (
              <AssistantMessage 
                content={msg.content} 
                blocks={msg.blocks} 
                status={msg.status}
                isThinking={msg.isThinking} 
                isGroupStart={msg.isGroupStart}
                isGroupEnd={msg.isGroupEnd}
                onRegenerate={() => setRegenerateMessageId(msg.id)}
              />
            )}
          </motion.div>
        ))}
        <div ref={bottomRef} className="h-4 w-full" />
      </div>

      {isAutoScrollPaused && (
        <button
          onClick={jumpToBottom}
          className="fixed bottom-24 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-[var(--bg-elevated)] border border-[var(--border-strong)] shadow-[var(--shadow-elevated)] rounded-full px-4 py-2 text-sm font-medium hover:bg-[var(--bg-surface)] transition-standard z-30"
        >
          <ArrowDown className="w-4 h-4" />
          {streamingStatus === "streaming" ? "New response..." : "Jump to latest"}
        </button>
      )}
    </div>
  );
}
"@
Set-Content -Path frontend\components\chat\MessageList.tsx -Value $code
