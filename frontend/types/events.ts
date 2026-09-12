export type SSEEvent =
  | { type: "message_start"; data: { message_id: string; role: string } }
  | { type: "content_block_start"; data: { index: number; type: string } }
  | { type: "content_block_delta"; data: { index: number; delta: { type: string; text?: string; content?: string } } }
  | { type: "content_block_stop"; data: { index: number } }
  | { type: "message_delta"; data: { delta: any } }
  | { type: "message_stop"; data: { message_id: string } }
  | { type: "error"; data: { message: string } };
