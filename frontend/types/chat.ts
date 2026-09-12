export interface SourceCitation {
  id: string;
  url: string;
  title: string;
  snippet?: string;
  metadata?: Record<string, string>;
}

export type BlockType = "markdown" | "code" | "table" | "chart" | "tool_call" | "tool_result";

export interface Block {
  type: BlockType;
  data: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  status: "pending" | "streaming" | "completed" | "error";
  content: string;
  blocks: Block[];
  sources: SourceCitation[];
  taskId?: string;
  createdAt: string;
  
  // Temporary legacy fields to avoid breaking other components immediately:
  metadata?: Record<string, unknown>;
  isStreaming?: boolean;
  statusMessage?: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, unknown>;
}
