import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallbackContent: string;
}

interface State {
  hasError: boolean;
}

export class ResponseErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(_: Error): State {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    if (process.env.NODE_ENV !== "production") {
      console.error("Markdown parsing error (safely caught):", error, errorInfo);
    }
  }

  public render() {
    if (this.state.hasError) {
      return (
        <pre className="whitespace-pre-wrap font-sans text-[16px] leading-[1.65] text-text-primary">
          {this.props.fallbackContent}
        </pre>
      );
    }

    return this.props.children;
  }
}
