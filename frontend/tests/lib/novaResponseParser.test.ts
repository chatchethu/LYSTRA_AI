import { parseNovaEvent } from '../../lib/novaResponseParser';

describe('novaResponseParser', () => {
  it('should return null for invalid JSON', () => {
    expect(parseNovaEvent('{ invalid json }')).toBeNull();
  });

  it('should parse status events', () => {
    expect(parseNovaEvent(JSON.stringify({ type: 'status', status: 'thinking' }))).toEqual({ type: 'status', status: 'thinking', message: undefined });
    expect(parseNovaEvent(JSON.stringify({ type: 'status', status: 'error', message: 'failed' }))).toEqual({ type: 'status', status: 'error', message: 'failed' });
    expect(parseNovaEvent(JSON.stringify({ type: 'status', status: 'done' }))).toEqual({ type: 'status', status: 'done' });
  });

  it('should parse legacy done/error events', () => {
    expect(parseNovaEvent(JSON.stringify({ type: 'done' }))).toEqual({ type: 'status', status: 'done' });
    expect(parseNovaEvent(JSON.stringify({ type: 'error', message: 'test error' }))).toEqual({ type: 'status', status: 'error', message: 'test error' });
  });

  it('should parse text events', () => {
    expect(parseNovaEvent(JSON.stringify({ type: 'text', text: 'hello' }))).toEqual({ type: 'text', text: 'hello' });
    expect(parseNovaEvent(JSON.stringify({ type: 'text', text: '' }))).toBeNull(); // Empty text returns null
  });

  it('should parse sources events', () => {
    expect(parseNovaEvent(JSON.stringify({ type: 'sources', sources: [{ id: 1 }] }))).toEqual({ type: 'sources', sources: [{ id: 1 }] });
  });

  it('should ignore metadata events', () => {
    expect(parseNovaEvent(JSON.stringify({ type: 'metadata', data: {} }))).toBeNull();
  });

  it('should parse chunk fallback', () => {
    expect(parseNovaEvent(JSON.stringify({ chunk: 'hello' }))).toEqual({ type: 'text', text: 'hello' });
    expect(parseNovaEvent(JSON.stringify({ chunk: '' }))).toBeNull();
  });

  it('should parse blocks_update fallback', () => {
    const blocks = [{ type: 'code', data: 'print("hi")' }];
    expect(parseNovaEvent(JSON.stringify({ blocks_update: { blocks } }))).toEqual({ type: 'structured', blocks });
  });

  it('should parse searchState fallback', () => {
    expect(parseNovaEvent(JSON.stringify({ searchState: { status: 'searching' } }))).toEqual({ type: 'status', status: 'thinking' });
    expect(parseNovaEvent(JSON.stringify({ searchState: { status: 'complete', sources: [1, 2] } }))).toEqual({ type: 'sources', sources: [1, 2] });
  });

  it('should parse error fallback', () => {
    expect(parseNovaEvent(JSON.stringify({ error: 'fatal' }))).toEqual({ type: 'status', status: 'error', message: 'fatal' });
  });
});
