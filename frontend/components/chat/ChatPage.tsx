"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { MessageList } from "./MessageList";
import { ChatComposer } from "./ChatComposer";
import { ChatHeader } from "./ChatHeader";
import { TaskPanel } from "./TaskPanel";
import { useChatStore } from "@/store/chatStore";
import { useAuth } from "@/components/auth/AuthProvider";
import { AuthModal } from "@/components/auth/AuthModal";
import { conversationsClient } from "@/lib/api/conversations";
import { useState } from "react";

// Fix #8: Typed shape that matches what the API actually returns (snake_case dates).
// The store's ChatMessage uses camelCase, so we map explicitly below.
interface RawApiMessage {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  created_at: string;
  blocks?: unknown;
}

interface ChatPageProps {
  conversationId?: string;
}

export function ChatPage({ conversationId: routeId }: ChatPageProps) {
  const router = useRouter();

  // Fix #1: isAuthLoaded is now used to gate the fetch (see Fix #3). useSearchParams removed.
  const { isAuthenticated, isAuthLoaded } = useAuth();

  const [showAuthModal, setShowAuthModal] = useState(false);

  const storeConversationId = useChatStore(state => state.conversationId);
  const setConversationId = useChatStore(state => state.setConversationId);
  const setMessages = useChatStore(state => state.setMessages);
  const clearChat = useChatStore(state => state.clearChat);
  const setLoadingHistory = useChatStore(state => state.setLoadingHistory);
  const setError = useChatStore(state => state.setError);

  // Fix #2: Renamed from isMounted (which shadowed the local let below) to isMountedRef.
  const isMountedRef = useRef(false);
  const prevRouteId = useRef(routeId);
  const prevStoreId = useRef(storeConversationId);

  // ── Route ↔ Store sync ────────────────────────────────────────────────────
  // On mount: URL is source of truth. After mount: distinguish user navigation
  // from app-created conversations via ref tracking.
  useEffect(() => {
    if (!isMountedRef.current) {
      if (routeId !== storeConversationId) {
        setConversationId(routeId || null);
      }
      isMountedRef.current = true;
      return;
    }

    // 1. User navigated → sync route into store
    if (routeId !== prevRouteId.current) {
      setConversationId(routeId || null);
    }
    // 2. App created a new chat → push new ID into the URL
    else if (storeConversationId !== prevStoreId.current) {
      if (storeConversationId !== routeId) {
        router.replace(storeConversationId ? `/chat/${storeConversationId}` : `/chat`);
      }
    }

    prevRouteId.current = routeId;
    prevStoreId.current = storeConversationId;
  }, [routeId, storeConversationId, setConversationId, router]);

  // Active conversation ID (store wins over prop — store is source of truth post-mount)
  const activeId = storeConversationId || routeId;

  // ── History fetch ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!activeId) {
      clearChat();
      return;
    }

    // Fix #3: Gate on isAuthLoaded so we never try to fetch before auth settles.
    // If auth hasn't loaded yet this effect will re-run when isAuthLoaded flips true.
    if (!isAuthLoaded) return;

    if (!isAuthenticated) {
      // Auth resolved as logged-out — show the auth modal instead of a blank screen.
      setShowAuthModal(true);
      return;
    }

    // Fix #6: AbortController cancels the in-flight fetch when the user switches
    // conversations rapidly. Previously the fetch always completed, wasting bandwidth.
    const controller = new AbortController();

    // Fix #2 (local variable): renamed to `isActive` so it no longer shadows isMountedRef.
    let isActive = true;

    const loadConversation = async () => {
      // Fix #5: signal loading so MessageList can show a skeleton
      setLoadingHistory(true);
      setError(null);

      try {
        const data = await conversationsClient.getMessages(activeId, controller.signal);

        // Fix #2: use isActive instead of isMounted to avoid naming confusion
        if (!isActive) return;

        // Fix #8: data is typed as Message[] from the API client, but the raw wire
        // format uses snake_case. Map explicitly so a future API rename is a compile error.
        const formatted = (data as unknown as RawApiMessage[]).map((m) => {
          let blocks: unknown[] = [];
          if (m.role === "assistant") {
            // Only attempt JSON parse if the content is a JSON array of objects.
            // "[{" is the canonical shape of a NovaBlock array from the backend.
            // This guards against:
            //  - Markdown numbered lists: "[1] First item..."
            //  - LLM error strings:       "[Error: could not prepare response.]"
            //  - Any other plain text that happens to start with "["
            const trimmedContent = m.content.trimStart();
            if (trimmedContent.startsWith("[{") && trimmedContent.trimEnd().endsWith("}]")) {
              try {
                const parsed = JSON.parse(m.content);
                blocks = Array.isArray(parsed) ? parsed : (parsed.blocks ?? []);
              } catch {
                // Malformed JSON that passed the heuristic — silently treat as plain text.
              }
            }
          }
          return {
            id: m.id,
            role: m.role as "user" | "assistant" | "system",
            content: m.content,
            blocks: blocks.length > 0 ? (blocks as any) : undefined,
            status: "completed" as const,
            createdAt: m.created_at,
          };
        });

        // Preserve any messages currently streaming or pending — they arrived after
        // the fetch started and must not be overwritten. (Prevents the race where a
        // fast user sends a message while history is still loading.)
        setMessages((prev) => {
          const liveMessages = prev.filter(
            (p) => p.status === "streaming" || p.status === "pending"
          );
          return [...formatted, ...liveMessages];
        });
      } catch (err: unknown) {
        if (!isActive) return;

        // Fix #6: Abort errors are expected and silent — they mean we switched conversations.
        if (err instanceof Error && err.name === "AbortError") return;

        // Fix #4: Distinguish auth failures from generic errors.
        const apiError = err as any;
        if (apiError?.status === 401 || apiError?.status === 403) {
          // The API client already handles token refresh and redirects for 401s.
          // If we still get here it means the session is truly invalid — show auth modal.
          setShowAuthModal(true);
        } else {
          // Fix #4 + #9: surface a real error in the store (not just console.warn)
          // so the UI can render an inline error state with a retry option.
          const message =
            typeof apiError?.message === "string"
              ? apiError.message
              : "Failed to load conversation. Please try again.";
          setError(message);
          // Fix #9: use console.error (not warn) so it shows in monitoring tools;
          // swap for Sentry.captureException(err) / your logger in production.
          console.error("[ChatPage] Failed to load conversation history:", err);
        }
      } finally {
        if (isActive) setLoadingHistory(false);
      }
    };

    loadConversation();

    return () => {
      isActive = false;
      controller.abort(); // Fix #6: cancel the fetch, not just ignore the response
    };

    // Fix #7: setMessages, clearChat, setLoadingHistory, setError are stable Zustand
    // action references (they never change identity), so listing them here is both
    // correct and safe for the exhaustive-deps lint rule.
  }, [activeId, isAuthenticated, isAuthLoaded, setMessages, clearChat, setLoadingHistory, setError]);

  return (
    <div className="relative flex-1 flex flex-col w-full h-full bg-background overflow-hidden">
      <ChatHeader />
      <TaskPanel />
      <MessageList />
      <ChatComposer onShowAuth={() => setShowAuthModal(true)} />

      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
        />
      )}
    </div>
  );
}
