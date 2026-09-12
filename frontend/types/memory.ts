export interface Memory {
  id: string;
  content: string;
  memory_type: string;
  created_at: string;
  importance?: number;
  source?: string;
  metadata?: Record<string, any>;
}
