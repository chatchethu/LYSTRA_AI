export type NovaTextResponse = { type: 'text'; text: string; };

export type NovaBlock = { id?: string; type: string; data?: any; metadata?: any; };

export type NovaStructuredResponse = { type: 'structured'; blocks: NovaBlock[]; };

export type NovaStatusResponse = { type: 'status'; status: 'idle' | 'thinking' | 'streaming' | 'done' | 'error'; message?: string; };

export type NovaSourcesResponse = { type: 'sources'; sources: any[]; };

export type NovaParsedEvent = NovaTextResponse | NovaStructuredResponse | NovaStatusResponse | NovaSourcesResponse;

export function parseNovaEvent(raw: string): NovaParsedEvent | null {
  let data: any;
  try { data = JSON.parse(raw); } catch { return null; }
  
  // Handle new CanonicalEvent structure (has event_type and payload)
  if (data.event_type && data.payload) {
    const payload = data.payload;
    if (data.event_type === 'run.failed') {
      return { type: 'status', status: 'error', message: payload.error || 'An error occurred.' };
    }
    if (data.event_type === 'run.completed' || data.event_type === 'message.completed') {
      return { type: 'status', status: 'done' };
    }
    if (data.event_type === 'agent.thinking') {
      return { type: 'status', status: 'thinking', message: payload.status || 'Thinking...' };
    }
    if (data.event_type === 'message.delta' || data.event_type === 'message.completed') {
      // The payload.content is the blocks JSON string
      if (payload.content) {
         try {
            const parsedBlocks = JSON.parse(payload.content);
            if (Array.isArray(parsedBlocks)) {
               return { type: 'structured', blocks: parsedBlocks };
            }
         } catch(e) {
            return { type: 'text', text: payload.content };
         }
      }
    }
  }

  // Legacy format support
  if (data.type === 'status') {
    const s: string = data.status || '';
    if (s === 'error') return { type: 'status', status: 'error', message: data.message };
    if (s === 'done') return { type: 'status', status: 'done' };
    return { type: 'status', status: 'thinking', message: data.message };
  }
  if (data.type === 'done') return { type: 'status', status: 'done' };
  if (data.type === 'error') return { type: 'status', status: 'error', message: data.message || 'An error occurred.' };
  if (data.type === 'text') {
    return typeof data.text === 'string' && data.text ? { type: 'text', text: data.text } : null;
  }
  if (data.type === 'sources') return { type: 'sources', sources: data.sources || [] };
  if (data.type === 'metadata') return null;

  if (typeof data.chunk === 'string') {
    return data.chunk.length > 0 ? { type: 'text', text: data.chunk } : null;
  }
  if (data.blocks_update && Array.isArray(data.blocks_update.blocks)) {
    return { type: 'structured', blocks: data.blocks_update.blocks };
  }
  if (Array.isArray(data.blocks) && data.blocks.length > 0) {
    return { type: 'structured', blocks: data.blocks };
  }
  if (data.searchState) {
    if (data.searchState.status === 'searching') return { type: 'status', status: 'thinking' };
    if (data.searchState.status === 'complete') return { type: 'sources', sources: data.searchState.sources || [] };
    return null;
  }
  if (data.error) return { type: 'status', status: 'error', message: String(data.error) };
  return null;
}
