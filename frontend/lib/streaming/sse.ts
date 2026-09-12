// frontend/lib/streaming/sse.ts

export interface SSEEvent {
  id?: string;
  event?: string;
  data: string;
}

export class SSEParser {
  private buffer: string = '';

  public parse(chunk: string): SSEEvent[] {
    this.buffer += chunk.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    const events: SSEEvent[] = [];

    let doubleNewlineIdx: number;
    while ((doubleNewlineIdx = this.buffer.indexOf('\n\n')) !== -1) {
      const rawEvent = this.buffer.slice(0, doubleNewlineIdx);
      this.buffer = this.buffer.slice(doubleNewlineIdx + 2);

      const parsed = this.parseEvent(rawEvent);
      if (parsed) {
        events.push(parsed);
      }
    }

    return events;
  }

  private parseEvent(rawEvent: string): SSEEvent | null {
    const lines = rawEvent.split('\n');
    let id: string | undefined;
    let event: string | undefined;
    const dataLines: string[] = [];

    for (const line of lines) {
      if (!line || line.startsWith(':')) continue; // Skip comments

      const colonIdx = line.indexOf(':');
      if (colonIdx === -1) continue;

      const field = line.slice(0, colonIdx).trim();
      const value = line.slice(colonIdx + 1).replace(/^ /, '');

      if (field === 'id') {
        id = value;
      } else if (field === 'event') {
        event = value;
      } else if (field === 'data') {
        dataLines.push(value);
      }
    }

    if (dataLines.length > 0 || event) {
      return {
        id,
        event,
        data: dataLines.join('\n'),
      };
    }
    return null;
  }
}
