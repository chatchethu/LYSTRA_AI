import { 
  ResponseBlock, 
  ParagraphBlock, 
  HeadingBlock, 
  BulletListBlock, 
  NumberedListBlock, 
  CodeBlock, 
  TableBlock, 
  BlockquoteBlock, 
  DividerBlock 
} from "../types/blocks";

// Phase RL-04: Response Normalization Layer
export function normalizeResponse(raw: string): string {
  if (!raw) return "";
  let text = raw.replace(/\r\n/g, "\n");
  text = text.replace(/\n{3,}/g, "\n\n");
  return text.trim();
}

// Phase RL-05 -> RL-10: Markdown Parser & Block Detection
export function parseMarkdownToBlocks(markdown: string): ResponseBlock[] {
  const normalized = normalizeResponse(markdown);
  const blocks: ResponseBlock[] = [];
  
  if (!normalized) return blocks;

  let currentText = normalized;

  const codeBlockRegex = /^```([a-zA-Z0-9+-]*)\n([\s\S]*?)```/m;
  const headingRegex = /^(#{1,6})\s+(.+)$/m;
  const blockquoteRegex = /^((?:> .*\n?)+)/m;
  const dividerRegex = /^(?:---|\*\*\*|___)\s*$/m;
  const tableRegex = /^((?:\|[^\n]+\|\n)((?:\|[-:]+)+\|\n)(?:\|[^\n]+\|\n?)+)/m;
  const bulletListRegex = /^((?:[ \t]*[-*+]\s+.*\n?)+)/m;
  const numberedListRegex = /^((?:[ \t]*\d+\.\s+.*\n?)+)/m;

  while (currentText.length > 0) {
    const nextCode = currentText.match(codeBlockRegex);
    const nextTable = currentText.match(tableRegex);
    
    const splitIndex = currentText.indexOf("\n\n");
    let blockContent = "";
    
    if (nextCode && nextCode.index === 0) {
      blockContent = nextCode[0];
      blocks.push({
        type: "code",
        language: nextCode[1].trim(),
        content: nextCode[2].trim()
      } as CodeBlock);
      currentText = currentText.slice(blockContent.length).trimStart();
      continue;
    }

    if (nextTable && nextTable.index === 0) {
      blockContent = nextTable[0];
      const lines = blockContent.trim().split("\n");
      const headers = lines[0].split("|").filter(c => c.trim() !== "").map(c => c.trim());
      const rows = lines.slice(2).map(row => row.split("|").filter(c => c.trim() !== "").map(c => c.trim()));
      blocks.push({
        type: "table",
        headers,
        rows
      } as TableBlock);
      currentText = currentText.slice(blockContent.length).trimStart();
      continue;
    }

    if (splitIndex !== -1 && (!nextCode || splitIndex < nextCode.index!) && (!nextTable || splitIndex < nextTable.index!)) {
      blockContent = currentText.slice(0, splitIndex).trim();
      currentText = currentText.slice(splitIndex + 2).trimStart();
    } else {
      blockContent = currentText.trim();
      currentText = "";
    }

    if (!blockContent) continue;

    const headingMatch = blockContent.match(headingRegex);
    if (headingMatch && headingMatch[0] === blockContent) {
      blocks.push({
        type: "heading",
        level: headingMatch[1].length as any,
        content: headingMatch[2].trim()
      } as HeadingBlock);
      continue;
    }

    const bulletMatch = blockContent.match(bulletListRegex);
    if (bulletMatch && bulletMatch[0].trim() === blockContent) {
      const items = blockContent.split(/\n/).filter(i => i.trim());
      blocks.push({ type: "bullet-list", items } as BulletListBlock);
      continue;
    }

    const numberedMatch = blockContent.match(numberedListRegex);
    if (numberedMatch && numberedMatch[0].trim() === blockContent) {
      const items = blockContent.split(/\n/).filter(i => i.trim());
      blocks.push({ type: "numbered-list", items } as NumberedListBlock);
      continue;
    }

    const quoteMatch = blockContent.match(blockquoteRegex);
    if (quoteMatch && quoteMatch[0].trim() === blockContent) {
      blocks.push({
        type: "blockquote",
        content: blockContent.split("\n").map(l => l.replace(/^>\s?/, "")).join("\n")
      } as BlockquoteBlock);
      continue;
    }

    if (dividerRegex.test(blockContent)) {
      blocks.push({ type: "divider" } as DividerBlock);
      continue;
    }

    blocks.push({ type: "paragraph", content: blockContent } as ParagraphBlock);
  }

  return blocks;
}
