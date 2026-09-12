"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { useChatStore } from "@/store/chatStore";
import { StreamManager } from "@/lib/streaming/streamManager";
import { Send, Square, Plus, Mic, Paperclip, X, Loader2, MessageSquareReply } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";

interface ChatComposerProps {
  onShowAuth: () => void;
}

export function ChatComposer({ onShowAuth }: ChatComposerProps) {
  const [input, setInput] = useState("");
  const [showMentions, setShowMentions] = useState(false);
  const [mentionQuery, setMentionQuery] = useState("");
  const [attachments, setAttachments] = useState<{ name: string, status: "uploading" | "processing" | "ready" }[]>([]);
  const [voiceState, setVoiceState] = useState<"idle" | "recording" | "processing">("idle");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const streamManagerRef = useRef<StreamManager | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { isAuthenticated } = useAuth();

  const conversationId = useChatStore(state => state.conversationId);
  const isGenerating = useChatStore(state => state.isGenerating);
  const addMessage = useChatStore(state => state.addMessage);
  const messages = useChatStore(state => state.messages);
  const regenerateMessageId = useChatStore(state => state.regenerateMessageId);
  const setRegenerateMessageId = useChatStore(state => state.setRegenerateMessageId);
  const replyToMessageId = useChatStore(state => state.replyToMessageId);
  const setReplyToMessageId = useChatStore(state => state.setReplyToMessageId);
  const replyMessage = messages.find(m => m.id === replyToMessageId);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  // Phase 19: Offline Queue Recovery
  const offlineQueue = useChatStore(state => state.offlineQueue);
  const clearOfflineQueue = useChatStore(state => state.clearOfflineQueue);

  useEffect(() => {
    const handleOnline = async () => {
      if (offlineQueue && offlineQueue.length > 0) {
        // Send the queued messages
        for (const msg of offlineQueue) {
          await executeStream(msg);
        }
        clearOfflineQueue();
      }
    };

    window.addEventListener('online', handleOnline);
    return () => window.removeEventListener('online', handleOnline);
  }, [offlineQueue, clearOfflineQueue]);

  // Handle Regeneration
  useEffect(() => {
    if (regenerateMessageId && !isGenerating) {
      const idx = messages.findIndex(m => m.id === regenerateMessageId);
      if (idx > 0) {
        // Find the user message before this assistant message
        let userMsg = null;
        for (let i = idx - 1; i >= 0; i--) {
          if (messages[i].role === "user") {
            userMsg = messages[i];
            break;
          }
        }

        if (userMsg) {
          // Trigger generation with this text
          setRegenerateMessageId(null);
          // Mark the old assistant message as replaced or just let startStream create a new one
          // We will create a new assistant message and stream to it. The product requirement (FE-38) says "preserve previous response if product design supports it" or just append new run.
          // Let's just run a new generation. The backend will append a new assistant message.
          executeStream(userMsg.content);
        }
      }
      setRegenerateMessageId(null);
    }
  }, [regenerateMessageId, isGenerating, messages, setRegenerateMessageId]);

  // Listen to suggestions from MessageList
  useEffect(() => {
    const handleSuggest = (e: any) => {
      setInput(e.detail);
      if (inputRef.current) {
        inputRef.current.focus();
      }
    };
    window.addEventListener("lystra-suggest", handleSuggest);
    return () => window.removeEventListener("lystra-suggest", handleSuggest);
  }, []);

  const executeStream = async (userMessage: string) => {
    // FE-16: Prevent double-execution synchronously
    if (useChatStore.getState().isGenerating) return;
    useChatStore.getState().setGenerating(true);

    const tempAssistantId = crypto.randomUUID();

    // FE-13: Assistant Placeholder
    addMessage({
      id: tempAssistantId,
      role: "assistant",
      content: "",
      status: "streaming",
      isThinking: true,
      createdAt: new Date().toISOString()
    });

    try {
      const { chatClient } = await import("@/lib/api/chat");

      const manager = new StreamManager(conversationId, tempAssistantId);
      streamManagerRef.current = manager;

      await manager.startStream(userMessage, chatClient);
    } catch (e) {
      console.error(e);
    } finally {
      streamManagerRef.current = null;
    }
  };

  const enqueueOfflineMessage = useChatStore(state => state.enqueueOfflineMessage);

  const handleSend = async () => {
    // Guard: no empty input, no concurrent generation
    if (!input.trim() || useChatStore.getState().isGenerating) return;

    if (!isAuthenticated) {
      const stored = localStorage.getItem("nova_guest_count") || "0";
      const count = parseInt(stored, 10);
      if (count >= 4) {
        onShowAuth();
        return;
      }
      localStorage.setItem("nova_guest_count", (count + 1).toString());
    }

    const userMessage = input.trim();
    setInput("");
    setReplyToMessageId(null);

    // Phase 19: Offline Experience
    const isOnline = typeof window !== 'undefined' && window.navigator.onLine;

    const tempUserId = crypto.randomUUID();
    addMessage({
      id: tempUserId,
      role: "user",
      content: userMessage,
      status: isOnline ? "completed" : "pending",
      createdAt: new Date().toISOString()
    });

    if (!isOnline) {
      enqueueOfflineMessage(userMessage);
      return; // Stop here, message is queued in local state
    }

    await executeStream(userMessage);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleStop = () => {
    if (streamManagerRef.current) {
      streamManagerRef.current.stop();
    }
  };

  const handleVoiceClick = async () => {
    if (voiceState === "recording") {
      setVoiceState("processing");
      mediaRecorderRef.current?.stop();
      return;
    }

    try {
      if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
        throw new Error("Voice recording is not supported by this browser.");
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg"]
        .find(type => MediaRecorder.isTypeSupported(type)) || "";
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      audioChunksRef.current = [];
      mediaStreamRef.current = stream;
      mediaRecorderRef.current = recorder;
      recorder.ondataavailable = event => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };
      recorder.onstop = async () => {
        if (recordingTimerRef.current) clearTimeout(recordingTimerRef.current);
        const blob = new Blob(audioChunksRef.current, { type: recorder.mimeType || "audio/webm" });
        stream.getTracks().forEach(track => track.stop());
        mediaRecorderRef.current = null;
        mediaStreamRef.current = null;
        audioChunksRef.current = [];
        try {
          const extension = blob.type.includes("ogg") ? "ogg" : blob.type.includes("mp4") ? "m4a" : "webm";
          const formData = new FormData();
          formData.append("file", blob, `recording.${extension}`);
          const { ApiClient } = await import("@/lib/api/client");
          const response = await ApiClient.post<{ text: string }>("/api/v1/speech/transcribe", formData);
          setInput(prev => prev + (prev ? " " : "") + response.text);
        } catch (error) {
          console.error("Voice transcription failed", error);
          alert(error instanceof Error ? error.message : "Could not transcribe the recording.");
        } finally {
          setVoiceState("idle");
        }
      };
      recorder.start();
      recordingTimerRef.current = setTimeout(() => recorder.stop(), 29_000);
      setVoiceState("recording");
    } catch (error) {
      alert(error instanceof Error ? error.message : "Microphone permission denied. Please allow access in your browser settings.");
      setVoiceState("idle");
    }
  };

  useEffect(() => () => {
    if (recordingTimerRef.current) clearTimeout(recordingTimerRef.current);
    mediaRecorderRef.current?.stop();
    mediaStreamRef.current?.getTracks().forEach(track => track.stop());
  }, []);

  return (
    <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-background via-background/95 to-transparent pt-12 pb-6 px-4 z-20">
      <div className="max-w-3xl mx-auto relative flex flex-col gap-2">
        <div className="w-full bg-[var(--bg-elevated)] border border-[var(--border-strong)] rounded-[var(--radius-lg)] shadow-[var(--shadow-elevated)] flex flex-col focus-within:ring-2 focus-within:ring-primary/50 transition-all">
          {/* Phase 10: Mention Suggestions */}
          {showMentions && (
            <div className="absolute bottom-full mb-2 left-4 w-64 bg-[var(--bg-elevated)] border border-[var(--border-strong)] rounded-[var(--radius-md)] shadow-[var(--shadow-elevated)] overflow-hidden z-50 animate-fadeIn">
              <div className="px-3 py-2 text-xs font-semibold text-[var(--text-tertiary)] bg-[var(--bg-surface)] border-b border-[var(--border-subtle)] uppercase tracking-wider">
                Mention Agents
              </div>
              <div className="flex flex-col p-1">
                {['lystra', 'research', 'web']
                  .filter(m => m.includes(mentionQuery))
                  .map((mention, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        const words = input.split(" ");
                        words.pop();
                        setInput([...words, `@${mention} `].join(" ").trimStart());
                        setShowMentions(false);
                        inputRef.current?.focus();
                      }}
                      className="flex items-center gap-2 px-3 py-2 text-sm text-[var(--text-primary)] hover:bg-[var(--bg-surface)] rounded-md transition-colors text-left"
                    >
                      <div className="w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold text-[10px]">
                        {mention[0].toUpperCase()}
                      </div>
                      <span>@{mention}</span>
                    </button>
                  ))}
                {['lystra', 'research', 'web'].filter(m => m.includes(mentionQuery)).length === 0 && (
                  <div className="px-3 py-4 text-xs text-center text-[var(--text-tertiary)]">No agents found</div>
                )}
              </div>
            </div>
          )}

          {/* Phase 10: Reply Preview */}
          {replyMessage && (
            <div className="flex items-center justify-between px-4 py-2 bg-[var(--bg-surface)] border-b border-[var(--border-subtle)] rounded-t-[var(--radius-lg)]">
              <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)] truncate">
                <MessageSquareReply size={14} className="shrink-0" />
                <span className="font-medium shrink-0">Replying to {replyMessage.role === 'user' ? 'yourself' : 'LYSTRA'}</span>
                <span className="truncate opacity-70">: {replyMessage.content}</span>
              </div>
              <button onClick={() => setReplyToMessageId(null)} className="p-1 shrink-0 rounded-full hover:bg-[var(--bg-base)] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors">
                <X size={14} />
              </button>
            </div>
          )}

          {/* Attachments Preview */}
          {attachments.length > 0 && (
            <div className="flex flex-wrap gap-2 px-4 pt-3 pb-1 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]">
              {attachments.map((att, idx) => (
                <div key={idx} className="flex items-center gap-2 bg-white/[0.04] border border-white/[0.06] rounded-[var(--radius-lg)] shadow-[var(--shadow-elevated)] pl-3 pr-2 py-1.5 text-xs text-text-primary">
                  {att.status === "ready" ? (
                    <Paperclip size={14} className="text-text-muted" />
                  ) : (
                    <Loader2 size={14} className="text-primary animate-spin" />
                  )}
                  <span className="truncate max-w-[150px]">{att.name}</span>
                  <button
                    onClick={() => setAttachments(prev => prev.filter((_, i) => i !== idx))}
                    className="p-0.5 hover:bg-white/10 rounded-md transition-colors text-text-muted hover:text-error ml-1"
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-end w-full min-h-[50px] p-1">
            <button
              onClick={() => {
                setAttachments(prev => [...prev, { name: "report.pdf", status: "processing" }]);
                setTimeout(() => {
                  setAttachments(prev => prev.map((a, i) => i === prev.length - 1 ? { ...a, status: "ready" } : a));
                }, 2000);
              }}
              aria-label="Add attachment"
              className="mb-1 p-2.5 text-text-secondary hover:text-primary transition-colors shrink-0 rounded-xl hover:bg-white/[0.04] focus:ring-2 focus:ring-primary outline-none"
              title="Add attachment"
            >
              <Plus size={20} />
            </button>

              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => {
                  const val = e.target.value;
                  setInput(val);

                  // Phase 10: Mention Suggestions
                  const lastWord = val.split(" ").pop();
                  if (lastWord?.startsWith("@")) {
                    setShowMentions(true);
                    setMentionQuery(lastWord.slice(1).toLowerCase());
                  } else {
                    setShowMentions(false);
                  }
                }}
                onKeyDown={handleKeyDown}
                placeholder="Ask LYSTRA anything..."
                aria-label="Message input"
                className="flex-1 max-h-[200px] bg-transparent border-0 resize-none outline-none text-text-primary px-2 py-3 custom-scrollbar text-body font-body"
                rows={1}
              />

              <div className="shrink-0 p-1 flex items-center gap-1">
                {isGenerating ? (
                  <button
                    onClick={handleStop}
                    aria-label="Stop generating"
                    className="w-10 h-10 rounded-xl bg-surface border border-[var(--border-strong)] flex items-center justify-center text-text-primary hover:text-error transition-colors focus:ring-2 focus:ring-primary outline-none"
                  >
                    <Square size={16} fill="currentColor" />
                  </button>
                ) : (
                  <button
                    onClick={handleSend}
                    disabled={!input.trim()}
                    aria-label="Send message"
                    className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors focus:ring-2 focus:ring-primary/50 outline-none"
                  >
                    <Send size={18} />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
        <div className="text-center text-xs text-text-muted/70 font-medium tracking-wide">
          LYSTRA AI can make mistakes. Verify critical information.
        </div>
      </div>
  );
}
