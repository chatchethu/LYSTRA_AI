import React, { useState } from "react";
import { Copy, Check } from "lucide-react";
import clsx from "clsx";
import { useToast } from "./ToastContext";

interface CopyButtonProps {
  text: string;
  className?: string;
  showToastNotification?: boolean;
}

export function CopyButton({ text, className, showToastNotification = true }: CopyButtonProps) {
  const [isCopied, setIsCopied] = useState(false);
  const { showToast } = useToast();

  const handleCopy = async () => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setIsCopied(true);
      if (showToastNotification) {
        showToast("Copied to clipboard", "success");
      }
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy", err);
      if (showToastNotification) {
        showToast("Failed to copy to clipboard", "error");
      }
    }
  };

  return (
    <button
      onClick={handleCopy}
      title="Copy to clipboard"
      className={clsx(
        "p-1.5 flex items-center gap-1.5 rounded-md transition-colors text-xs font-medium",
        isCopied 
          ? "text-success hover:bg-success/10" 
          : "text-text-muted hover:text-text-primary hover:bg-white/5",
        className
      )}
    >
      {isCopied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
      {isCopied && <span>Copied</span>}
    </button>
  );
}
