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
  const isLoadingHistory = useChatStore(state => state.isLoadingHistory);
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  
  const [isAutoScrollPaused, setIsAutoScrollPaused] = useState(false);
  const [visibleCount, setVisibleCount] = useState(50); // Phase 31: Virtualization/Lazy Loading
  const setRegenerateMessageId = useChatStore(state => state.setRegenerateMessageId);
  const setReplyToMessageId = useChatStore(state => state.setReplyToMessageId);

  const handleScroll = () => {
    if (!scrollContainerRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    
    // Lazy load older messages when scrolling up
    if (scrollTop < 200 && visibleCount < messages.length) {
      setVisibleCount(prev => Math.min(prev + 50, messages.length));
    }
    
    const distanceToBottom = scrollHeight - scrollTop - clientHeight;
    
    // If the user scrolls up more than 50px from bottom, pause auto-scroll
    if (distanceToBottom > 50) {
      setIsAutoScrollPaused(true);
    } else {
      setIsAutoScrollPaused(false);
    }
  };

  // Smart auto-scroll
  useEffect(() => {
    if (!isAutoScrollPaused) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isAutoScrollPaused]);

  const jumpToBottom = () => {
    setIsAutoScrollPaused(false);
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const groupedMessages = useMemo(() => {
    return messages.map((msg, index) => {
      const prevMsg = messages[index - 1];
      const nextMsg = messages[index + 1];
      
      const isGroupStart = !prevMsg || prevMsg.role !== msg.role;
      const isGroupEnd = !nextMsg || nextMsg.role !== msg.role;
      
      return { ...msg, isGroupStart, isGroupEnd };
    });
  }, [messages]);

  // Show skeleton while history is loading to avoid a flash of the empty-state greeting
  if (isLoadingHistory && messages.length === 0) {
    return (
      <div
        className="flex-1 overflow-y-auto w-full custom-scrollbar pt-8 pb-32"
        aria-busy="true"
        aria-label="Loading conversation history"
      >
        <div className="max-w-3xl mx-auto px-4 flex flex-col gap-6">
          {[80, 55, 90].map((width, i) => (
            <div key={i} className={`flex ${i % 2 === 0 ? "justify-end" : "justify-start"}`}>
              <div
                className="h-10 rounded-2xl bg-white/5 animate-pulse"
                style={{ width: `${width}%` }}
              />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (messages.length === 0) {
    const hour = new Date().getHours();
    let greeting = "Good evening";
    if (hour < 12) greeting = "Good morning";
    else if (hour < 18) greeting = "Good afternoon";

    const suggestions = [
      { title: "Plan something", desc: "Create a schedule or project plan" },
      { title: "Brainstorm an idea", desc: "Generate creative concepts" },
      { title: "Solve a problem", desc: "Debug code or analyze logic" },
      { title: "Talk with me", desc: "Have a casual conversation" }
    ];

    const handleSuggest = (text: string) => {
      window.dispatchEvent(new CustomEvent("lystra-suggest", { detail: text }));
    };

    return (
      <div className="flex-1 flex flex-col items-center justify-center text-text-primary px-4 pb-20 mt-10">
        <div className="w-12 h-12 rounded-2xl bg-primary/20 flex items-center justify-center text-primary border border-primary/30 mb-6 shadow-lg shadow-primary/10">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-5.253 5.253 4 4 0 0 0 5.253 5.253 4 4 0 0 0 5.253 5.253 4 4 0 0 0 5.253-5.253 4 4 0 0 0 5.253-5.253 4 4 0 0 0-5.253-5.253 4 4 0 0 0-5.253-5.253 3 3 0 0 0-5.997-.125z"/></svg>
        </div>
        <h1 className="font-heading text-3xl font-bold mb-2 tracking-tight text-center bg-clip-text text-transparent bg-gradient-to-br from-white to-white/60">{greeting}.</h1>
        <p className="text-text-secondary text-lg mb-12 text-center max-w-md">What are you working on?</p>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => handleSuggest(s.title)}
              className="text-left p-4 rounded-xl bg-surface border border-border hover:bg-white/5 hover:border-primary/40 transition-all group flex flex-col gap-1"
            >
              <span className="text-sm font-semibold text-text-primary group-hover:text-primary transition-colors">{s.title}</span>
              <span className="text-xs text-text-muted">{s.desc}</span>
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={scrollContainerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto w-full custom-scrollbar pt-8 pb-32 relative"
    >
      <div className="max-w-3xl mx-auto px-4 flex flex-col gap-2">
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
                onReply={() => setReplyToMessageId(msg.id)}
              />
            ) : (
              <AssistantMessage 
                content={msg.content} 
                blocks={msg.blocks} 
                status={msg.status}
                isThinking={msg.isThinking} 
                isGroupStart={msg.isGroupStart}
                isGroupEnd={msg.isGroupEnd}
                onReply={() => setReplyToMessageId(msg.id)}
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
          className="fixed bottom-24 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-surface border border-border shadow-lg rounded-full px-4 py-2 text-sm font-medium text-text-primary hover:text-white hover:bg-surface-light hover:border-primary/50 transition-all animate-slideUp z-30"
        >
          <ArrowDown className="w-4 h-4" />
          {streamingStatus === "streaming" ? "New response..." : "Jump to latest"}
        </button>
      )}
    </div>
  );
}
