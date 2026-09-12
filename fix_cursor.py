with open('frontend/components/chat/markdown/ResponseRenderer.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the manual append
old_append = '''  // Phase RL-41: Inline Streaming Cursor
  if (isStreaming) {
    normalizedContent += " ▌";
  }'''
content = content.replace(old_append, '')

# Add the streaming cursor via CSS class
old_return = '''    <ResponseErrorBoundary fallbackContent={content}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
      className="text-text-primary text-[16px] leading-[1.65] break-words"'''

new_return = '''    <ResponseErrorBoundary fallbackContent={content}>
      <div className={isStreaming ? "streaming-response" : ""}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
      className="text-text-primary text-[16px] leading-[1.65] break-words"'''

old_end = '''    </ResponseErrorBoundary>
  );'''
new_end = '''      </ReactMarkdown>
      </div>
    </ResponseErrorBoundary>
  );'''

if old_return in content:
    content = content.replace(old_return, new_return)
    # the end might be different, let's replace by regex
    import re
    content = re.sub(r'</ReactMarkdown>\s*</ResponseErrorBoundary>', '      </ReactMarkdown>\n      </div>\n    </ResponseErrorBoundary>', content)
    with open('frontend/components/chat/markdown/ResponseRenderer.tsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated ResponseRenderer.")
else:
    print("Could not find blocks in ResponseRenderer.")
