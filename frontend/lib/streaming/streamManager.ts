import { SSEParser } from "./sse";
import { useChatStore, ChatMessage, NovaBlock } from "@/store/chatStore";

export class StreamManager {
  private parser: SSEParser;
  private abortController: AbortController | null = null;
  private currentResponseId: string;
  private conversationId: string | null;
  private chatRequestId: string | null = null;
  private lastEventId: string | null = null;
  private seenEventIds = new Set<string>();

  constructor(conversationId: string | null, responseMessageId: string) {
    this.parser = new SSEParser();
    this.currentResponseId = responseMessageId;
    this.conversationId = conversationId;
  }

  public stop() {
    if (this.abortController) {
      this.abortController.abort();
      useChatStore.getState().setStreamingStatus("idle");
      useChatStore.getState().setGenerating(false);
      useChatStore.getState().updateMessage(this.currentResponseId, { status: "cancelled", isThinking: false });
    }
  }

  public async startStream(userMessage: string, chatClient: any, retryCount = 0): Promise<void> {
    this.abortController = new AbortController();

    if (retryCount === 0) {
      useChatStore.getState().setStreamingStatus("connecting");
      useChatStore.getState().setGenerating(true);
    } else {
      useChatStore.getState().setStreamingStatus("reconnecting");
    }

    try {
      const response = await fetch(chatClient.streamUrl(), {
        method: "POST",
        headers: {
          ...chatClient.getStreamHeaders(),
          ...(this.chatRequestId ? { "X-Chat-Request-ID": this.chatRequestId } : {}),
          ...(this.lastEventId ? { "Last-Event-ID": this.lastEventId } : {}),
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_id: this.conversationId,
          stream: true
        }),
        credentials: "include",
        signal: this.abortController.signal
      });

      if (!response.ok) {
        throw new Error(`Stream connection failed: ${response.statusText}`);
      }

      this.chatRequestId = response.headers.get("X-Chat-Request-ID") || this.chatRequestId;

      useChatStore.getState().setStreamingStatus("streaming");

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No reader available");

      let isDone = false;
      while (!isDone) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const events = this.parser.parse(chunk);

        for (const event of events) {
          const eventType = event.event || "message";
          // Only replay-safe, server-assigned IDs can be deduplicated. Two
          // ID-less delta events may legitimately contain the same token.
          if (event.id && this.seenEventIds.has(event.id)) {
            continue;
          }
          if (event.id) this.seenEventIds.add(event.id);
          if (event.id) this.lastEventId = event.id;
          if (event.data === "[DONE]") {
            isDone = true;
            break;
          }

          try {
            const data = JSON.parse(event.data);
            // Accept both canonical SSE payloads and older {event, payload} envelopes.
            const normalizedType = data.type || data.event || eventType;
            const payload = data.payload && typeof data.payload === "object"
              ? {
                ...data.payload, ...Object.fromEntries(
                  ["conversation_id", "message_id", "task_id", "request_id"]
                    .filter((key) => data[key] !== undefined)
                    .map((key) => [key, data[key]])
                )
              }
              : data;
            this.handleEvent(normalizedType, payload);
          } catch (e) {
            // Ignore malformed JSON chunks within events
          }
        }
      }

      // If we finished without reading [DONE], the stream disconnected prematurely.
      // Reconnect if retry count < 3 and not manually aborted.
      if (!isDone && retryCount < 3 && !this.abortController.signal.aborted) {
        console.warn("Stream disconnected unexpectedly, reconnecting...");
        return this.startStream(userMessage, chatClient, retryCount + 1);
      }

    } catch (err: any) {
      if (err.name === "AbortError") {
        console.log("Stream aborted by user");
        // Status already set in stop()
      } else {
        console.error("Stream error:", err);
        if (retryCount < 3 && !this.abortController?.signal.aborted) {
          console.warn("Reconnecting due to error...");
          // Exponential backoff
          await new Promise(r => setTimeout(r, 1000 * Math.pow(2, retryCount)));
          return this.startStream(userMessage, chatClient, retryCount + 1);
        } else {
          useChatStore.getState().setError(err.message);
          useChatStore.getState().updateMessage(this.currentResponseId, { status: "failed", isThinking: false });
        }
      }
    } finally {
      // Always finalize the assistant message when stream ends completely (and not retrying)
      const store = useChatStore.getState();
      if (!store.error && store.streamingStatus !== "reconnecting" && !this.abortController?.signal.aborted) {
        const msg = store.messages.find(m => m.id === this.currentResponseId);
        if (msg && (msg.status === "streaming" || msg.status === "pending")) {
          store.updateMessage(this.currentResponseId, { status: "completed", isThinking: false });
        }
        store.setGenerating(false);
        store.setStreamingStatus("idle");
      }
    }
  }

  private handleEvent(eventType: string, data: any) {
    const store = useChatStore.getState();

    // 1. Ensure conversation ID sync
    if (data.conversation_id && store.conversationId !== data.conversation_id) {
      store.setConversationId(data.conversation_id);
      this.conversationId = data.conversation_id;
    }

    // 2. ID Reconciliation
    const backendMsgId = data.message_id || (data.payload && data.payload.message_id);
    if (backendMsgId && this.currentResponseId !== backendMsgId) {
      // Update ID to canonical backend ID
      store.updateMessage(this.currentResponseId, { id: backendMsgId });
      this.currentResponseId = backendMsgId;
      useChatStore.setState({ streamingMessageId: backendMsgId });
    }

    // 3. Delegate to Canonical Reducer (FE-16)
    store.dispatchStreamEvent(this.currentResponseId, eventType, data);
  }
}
