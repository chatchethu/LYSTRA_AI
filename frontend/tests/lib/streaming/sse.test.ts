import { SSEParser } from '../../../lib/streaming/sse';

describe('SSEParser', () => {
  let parser: SSEParser;

  beforeEach(() => {
    parser = new SSEParser();
  });

  it('should parse a simple complete event', () => {
    const chunk = 'event: message\ndata: {"hello":"world"}\n\n';
    const events = parser.parse(chunk);
    
    expect(events.length).toBe(1);
    expect(events[0].event).toBe('message');
    expect(events[0].data).toEqual('{"hello":"world"}');
  });

  it('should parse multiple events in one chunk', () => {
    const chunk = 'data: {"a":1}\n\nevent: update\ndata: {"b":2}\n\n';
    const events = parser.parse(chunk);
    
    expect(events.length).toBe(2);
    expect(events[0].data).toEqual('{"a":1}');
    expect(events[1].event).toBe('update');
    expect(events[1].data).toEqual('{"b":2}');
  });

  it('should handle fragmented events across multiple parse calls', () => {
    const chunk1 = 'event: mess';
    const chunk2 = 'age\ndata: {"foo"';
    const chunk3 = ':"bar"}\n\n';
    
    const events1 = parser.parse(chunk1);
    expect(events1.length).toBe(0);
    
    const events2 = parser.parse(chunk2);
    expect(events2.length).toBe(0);
    
    const events3 = parser.parse(chunk3);
    expect(events3.length).toBe(1);
    expect(events3[0].event).toBe('message');
    expect(events3[0].data).toEqual('{"foo":"bar"}');
  });

  it('should handle CRLF format', () => {
    const chunk = 'event: message\r\ndata: {"test":1}\r\n\r\n';
    const events = parser.parse(chunk);
    
    expect(events.length).toBe(1);
    expect(events[0].event).toBe('message');
    expect(events[0].data).toEqual('{"test":1}');
  });

  it('should parse [DONE] event properly', () => {
    const chunk = 'data: [DONE]\n\n';
    const events = parser.parse(chunk);
    
    expect(events.length).toBe(1);
    expect(events[0].data).toBe('[DONE]');
  });
});
