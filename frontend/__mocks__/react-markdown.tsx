import React from "react";

type MarkdownProps = {
    children?: React.ReactNode;
};

export default function ReactMarkdown({ children }: MarkdownProps) {
    return <div>{children}</div>;
}
