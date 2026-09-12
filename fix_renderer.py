import os

code = '''import React, { memo, useMemo } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import { CodeBlock } from "./CodeBlock";
import { normalizeResponse } from "../../../utils/responseNormalizer";
import { ResponseErrorBoundary } from "./ResponseErrorBoundary";

interface ResponseRendererProps {
  content: string;
  isStreaming?: boolean;
}

// 7. Extend sanitize schema for classes and task lists
const sanitizeSchema = {
  ...defaultSchema,
  attributes: {
    ...defaultSchema.attributes,
    code: [...(defaultSchema.attributes?.code || []), "className"],
    span: [...(defaultSchema.attributes?.span || []), "className"],
    input: [...(defaultSchema.attributes?.input || []), "type", "disabled", "checked"]
  },
  tagNames: [...(defaultSchema.tagNames || []), "input"]
};

// 4. Hoist components object to avoid remounting
// 11. Type safety with Components
const markdownComponents: Components = {
  // Phase RL-23 & RL-24: Paragraph spacing (~14px)
  p({ children, ...props }) {
    return <p className="mb-[14px] last:mb-0" {...props}>{children}</p>;
  },
  // Phase RL-23 & RL-24: Heading spacing (Heading->Paragraph ~10px)
  h1({ children, ...props }) {
    return <h1 className="text-[22px] font-bold mt-6 mb-3 text-text-primary leading-[1.3]" {...props}>{children}</h1>;
  },
  h2({ children, ...props }) {
    return <h2 className="text-[18px] font-semibold mt-5 mb-2.5 text-text-primary leading-[1.4]" {...props}>{children}</h2>;
  },
  h3({ children, ...props }) {
    return <h3 className="text-[16px] font-semibold mt-4 mb-2 text-text-primary leading-[1.5]" {...props}>{children}</h3>;
  },
  h4({ children, ...props }) {
    return <h4 className="text-[15px] font-medium mt-3 mb-2 text-text-primary" {...props}>{children}</h4>;
  },
  // Phase RL-25: List Spacing (indent, nested indent, item spacing)
  ul({ children, ...props }) {
    return <ul className="list-disc pl-5 mb-[14px] mt-1 space-y-1.5 marker:text-text-secondary" {...props}>{children}</ul>;
  },
  ol({ children, ...props }) {
    return <ol className="list-decimal pl-5 mb-[14px] mt-1 space-y-1.5 marker:text-text-secondary" {...props}>{children}</ol>;
  },
  li({ children, ...props }) {
    return <li className="pl-1.5 leading-[1.65]" {...props}>{children}</li>;
  },
  blockquote({ children, ...props }) {
    return (
      <blockquote className="border-l-4 border-primary/50 pl-4 py-1 my-4 bg-primary/5 rounded-r-md text-text-secondary italic" {...props}>
        {children}
      </blockquote>
    );
  },
  hr({ ...props }) {
    return <hr className="my-6 border-border" {...props} />;
  },
  strong({ children, ...props }) {
    return <strong className="font-semibold text-text-primary" {...props}>{children}</strong>;
  },
  em({ children, ...props }) {
    return <em className="italic" {...props}>{children}</em>;
  },
  // 1. Detect block-level by wrapping via the pre component instead of guessing from code
  pre({ children }) {
    const child = (children as React.ReactElement)?.props;
    if (child?.className) {
      const match = /language-(\\w+)/.exec(child.className);
      return (
        <div className="mb-4 mt-2">
          <CodeBlock language={match?.[1] ?? "text"} value={String(child.children).replace(/\\n$/, "")} />
        </div>
      );
    }
    return <pre>{children}</pre>;
  },
  code({ children, ...props }) {
    // 11. Remove any cast, safely omit node and inline which are standard react-markdown props
    const { node, inline, className, ...rest } = props as any;
    return (
      <code className="bg-white/10 px-1.5 py-0.5 rounded text-[0.85em] font-mono text-primary-light whitespace-pre-wrap break-words" className={className} {...rest}>
        {children}
      </code>
    );
  },
  table({ children, ...props }) {
    // 9. Tables have horizontal scroll container
    return (
      <div className="overflow-x-auto w-full my-4 rounded-lg border border-border">
        <table className="w-full text-sm text-left text-text-primary" {...props}>
          {children}
        </table>
      </div>
    );
  },
  th({ children, ...props }) {
    // 10. 	h cells missing scope="col"
    return (
      <th scope="col" className="px-4 py-3 bg-white/5 border-b border-border font-semibold" {...props}>
        {children}
      </th>
    );
  },
  td({ children, ...props }) {
    return (
      <td className="px-4 py-3 border-b border-border/50 bg-background/50" {...props}>
        {children}
      </td>
    );
  },
  a({ children, href, ...props }) {
    // Phase RL-16 & RL-17: Safe URL Handling
    if (href?.toLowerCase().trim().startsWith('javascript:')) {
      return <span className="text-error cursor-not-allowed" title="Unsafe link removed">[Unsafe Link Blocked]</span>;
    }
    return (
      <a 
        href={href}
        target="_blank" 
        rel="noopener noreferrer"
        className="text-primary hover:text-primary-light underline decoration-primary/30 hover:decoration-primary transition-colors underline-offset-2"
        {...props}
      >
        {children}
      </a>
    );
  },
  // 8. Add img renderer
  img({ src, alt, ...props }) {
    return <img src={src || ""} alt={alt || ""} loading="lazy" className="max-w-full rounded-md my-2" {...props} />;
  }
};

export const ResponseRenderer = memo(function ResponseRenderer({ content, isStreaming }: ResponseRendererProps) {
  // 2, 3, 5: normalizeResponse error boundary and memoization
  const normalizedContent = useMemo(() => {
    try {
      return normalizeResponse(content);
    } catch {
      return content;
    }
  }, [content]);

  return (
    <ResponseErrorBoundary fallbackContent={content}>
      <div className={isStreaming ? "streaming-response" : ""}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[[rehypeSanitize, sanitizeSchema]]}
          className="text-text-primary text-[16px] leading-[1.65] break-words"
          components={markdownComponents}
        >
          {normalizedContent}
        </ReactMarkdown>
      </div>
    </ResponseErrorBoundary>
  );
});
'''

with open('frontend/components/chat/markdown/ResponseRenderer.tsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("ResponseRenderer rewritten successfully.")
