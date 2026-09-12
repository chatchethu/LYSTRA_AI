// Phase RL-04: Response Normalization Layer
export function normalizeResponse(raw: string): string {
  if (!raw) return "";
  // Normalize line endings
  let text = raw.replace(/\r\n/g, "\n");
  
  // Normalize extra blank lines (more than 2 consecutive newlines) to exactly 2
  // This ensures blank-line-separated content becomes separate paragraphs (Phase RL-06)
  text = text.replace(/\n{3,}/g, "\n\n");
  
  // Fix missing spaces after list markers to ensure proper parsing
  text = text.replace(/^([-*+])([^\s])/gm, "$1 $2");
  text = text.replace(/^(\d+\.)([^\s])/gm, "$1 $2");
  
  // Fix missing blank lines before code blocks
  text = text.replace(/([^\n])\n```/g, "$1\n\n```");
  
  // Fix missing blank lines before headings
  text = text.replace(/([^\n])\n(#{1,6}\s)/g, "$1\n\n$2");

  // ── Defensive strip: Remove leaked internal LLM planning headers ─────────
  // Small models (Llama 3.2) sometimes print their internal reasoning stages
  // verbatim as italicised bullet points: "* User Request Validation*"
  // These are never valid user-facing content. Strip them unconditionally.
  //
  // Pattern covers:
  //   * Word Words*        (italic bullet — asterisk italic leak)
  //   * **Word Words**     (bold bullet header)
  //   - **Word Words**     (dash bold header)
  //   ## Word Words        (markdown h2/h3 acting as section label)
  //   **Word Words:**      (standalone bold label followed by colon)
  //
  // We only strip lines that look like pure heading/label lines (no prose after them).
  text = text
    // "* SomeLabel*" or "* SomeLabel *" on its own line
    .replace(/^\*\s+[A-Z][A-Za-z\s]+\*\s*$/gm, "")
    // "* **SomeLabel**" or "- **SomeLabel**" lines
    .replace(/^[*-]\s+\*{1,2}[A-Z][A-Za-z\s:]+\*{1,2}\s*$/gm, "")
    // "**SomeLabel:**" standalone bold labels with trailing colon
    .replace(/^\*{1,2}[A-Z][A-Za-z\s]+:\*{1,2}\s*$/gm, "");

  // Collapse any double-blank lines created by the stripping
  text = text.replace(/\n{3,}/g, "\n\n");
  
  return text.trim();
}
