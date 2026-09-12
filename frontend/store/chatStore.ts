import { create } from "zustand";

export type MessageStatus = "pending" | "streaming" | "completed" | "failed" | "cancelled";
export type MessageRole = "user" | "assistant" | "system";

import { ResponseBlock } from "../types/blocks";
export type NovaBlock = ResponseBlock; // Alias for backward compatibility

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  status: MessageStatus;
  blocks?: NovaBlock[];
  sources?: any[];
  taskId?: string;
  createdAt: string;
  isThinking?: boolean;
}

export interface ActiveTaskState {
  id: string;
  goal: string;
  step: number;
  totalSteps: number;
  currentAction: string;
}

export interface ChatState {
  conversationId: string | null;
  messages: ChatMessage[];
  activeTask: ActiveTaskState | null;
  streamingMessageId: string | null;
  streamingStatus: "idle" | "connecting" | "streaming" | "reconnecting" | "error";
  isGenerating: boolean;
  isLoadingHistory: boolean;            // true while fetching past messages for a conversation
  connectionState: "connected" | "disconnected";
  error: string | null;
  regenerateMessageId: string | null;
  offlineQueue: string[];
  replyToMessageId: string | null; // Phase 10: Intelligent Composer Reply State

  // Actions
  setConversationId: (id: string | null) => void;
  setReplyToMessageId: (id: string | null) => void;
  enqueueOfflineMessage: (msg: string) => void;
  clearOfflineQueue: () => void;
  setMessages: (messages: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void;
  addMessage: (message: ChatMessage) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  setGenerating: (isGenerating: boolean) => void;
  setStreamingStatus: (status: ChatState["streamingStatus"]) => void;
  setConnectionState: (state: ChatState["connectionState"]) => void;
  setError: (error: string | null) => void;
  setRegenerateMessageId: (id: string | null) => void;
  setActiveTask: (task: ActiveTaskState | null) => void;
  setLoadingHistory: (loading: boolean) => void;
  clearChat: () => void;
  dispatchStreamEvent: (messageId: string, eventType: string, payload: any) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversationId: null,
  messages: [],
  activeTask: null,
  streamingMessageId: null,
  streamingStatus: "idle",
  isGenerating: false,
  isLoadingHistory: false,
  connectionState: "connected",
  error: null,
  regenerateMessageId: null,
  offlineQueue: [],
  replyToMessageId: null,

  setConversationId: (id) => set({ conversationId: id }),
  setReplyToMessageId: (id) => set({ replyToMessageId: id }),
  enqueueOfflineMessage: (msg) => set((state) => ({ offlineQueue: [...state.offlineQueue, msg] })),
  clearOfflineQueue: () => set({ offlineQueue: [] }),
  setMessages: (update) => set((state) => ({
    messages: typeof update === "function" ? update(state.messages) : update
  })),
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  updateMessage: (id, updates) => set((state) => ({
    messages: state.messages.map((m) => (m.id === id ? { ...m, ...updates } : m))
  })),
  setGenerating: (isGenerating) => set({ isGenerating }),
  setStreamingStatus: (status) => set({ streamingStatus: status }),
  setConnectionState: (state) => set({ connectionState: state }),
  setError: (error) => set({ error }),
  setRegenerateMessageId: (id) => set({ regenerateMessageId: id }),
  setActiveTask: (task) => set({ activeTask: task }),
  setLoadingHistory: (loading) => set({ isLoadingHistory: loading }),
  clearChat: () => set({ messages: [], conversationId: null, error: null, regenerateMessageId: null,
  offlineQueue: [],
  replyToMessageId: null, isGenerating: false, streamingStatus: "idle", activeTask: null, isLoadingHistory: false }),

  dispatchStreamEvent: (messageId, eventType, payload) => {
    set((state) => {
      const msgs = state.messages;
      const msgIndex = msgs.findIndex(m => m.id === messageId);
      if (msgIndex === -1) return state;

      const msg = msgs[msgIndex];
      let updatedMsg = { ...msg };

      switch (eventType) {
        case "message.delta":
        case "message.chunk":
          // Backend sends {content: "..."} or {delta: "..."}
          const deltaText = payload.delta || payload.content || payload.text || "";
          const currentContent = updatedMsg.content || "";
          
          // If deltaText is the entire accumulated string so far (some backends do this)
          if (deltaText.length > currentContent.length && deltaText.startsWith(currentContent)) {
            updatedMsg.content = deltaText;
          } else {
            // Standard delta appending
            updatedMsg.content = currentContent + deltaText;
          }
          
          updatedMsg.isThinking = false;
          break;
        case "message.replace":
          updatedMsg.content = payload.content || payload.text || "";
          updatedMsg.isThinking = false;
          break;
        case "message.structured":
          updatedMsg.blocks = payload.blocks || [];
          updatedMsg.isThinking = false;
          break;
        case "message.completed":
          // Backend sends final content here too
          if (payload.content && !updatedMsg.content) {
            updatedMsg.content = payload.content;
          }
          updatedMsg.status = "completed";
          updatedMsg.isThinking = false;
          break;
        case "agent.thinking":
          // Update thinking status but don't change content
          updatedMsg.isThinking = true;
          break;
        case "run.completed":
          // Ensure message is finalized
          updatedMsg.status = "completed";
          updatedMsg.isThinking = false;
          break;
        case "run.failed":
          updatedMsg.status = "failed";
          updatedMsg.isThinking = false;
          break;
        default:
          return state; // No-op for unknown events
      }

      const newMessages = [...msgs];
      newMessages[msgIndex] = updatedMsg;
      return { messages: newMessages };
    });
  }
}));

// Cross-tab synchronization
if (typeof window !== "undefined") {
  const channel = new BroadcastChannel("nova_chat_sync");

  // Listen for changes from other tabs
  channel.onmessage = (event) => {
    const { type, payload } = event.data;

    if (type === "SYNC_CONVERSATION_ID") {
      const current = useChatStore.getState().conversationId;
      if (current !== payload) {
        useChatStore.setState({ conversationId: payload });
      }
    } else if (type === "SYNC_ACTIVE_TASK") {
      useChatStore.setState({ activeTask: payload });
    }
  };

  // Subscribe to local state changes to broadcast to other tabs
  useChatStore.subscribe((state, prevState) => {
    if (state.conversationId !== prevState.conversationId) {
      channel.postMessage({ type: "SYNC_CONVERSATION_ID", payload: state.conversationId });
    }
    if (state.activeTask?.id !== prevState.activeTask?.id) {
      channel.postMessage({ type: "SYNC_ACTIVE_TASK", payload: state.activeTask });
    }
  });
}
