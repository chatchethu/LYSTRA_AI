export type ResponseBlock =
  | ParagraphBlock
  | HeadingBlock
  | BulletListBlock
  | NumberedListBlock
  | CodeBlock
  | TableBlock
  | BlockquoteBlock
  | DividerBlock
  | ToolBlock
  | GenericBlock;

export interface ParagraphBlock {
  type: "paragraph";
  content: string;
}

export interface HeadingBlock {
  type: "heading";
  level: 1 | 2 | 3 | 4 | 5 | 6;
  content: string;
}

export interface BulletListBlock {
  type: "bullet-list";
  items: string[];
}

export interface NumberedListBlock {
  type: "numbered-list";
  items: string[];
}

export interface CodeBlock {
  type: "code";
  language?: string;
  content: string;
}

export interface TableBlock {
  type: "table";
  headers: string[];
  rows: string[][];
}

export interface BlockquoteBlock {
  type: "blockquote";
  content: string;
}

export interface DividerBlock {
  type: "divider";
}

export interface ToolBlock {
  type: "tool";
  name?: string;
  status?: string;
  input?: any;
  output?: any;
  error?: string;
}

export interface GenericBlock {
  type: string;
  data?: any;
  metadata?: any;
  [key: string]: any;
}
