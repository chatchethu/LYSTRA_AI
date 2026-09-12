import React, { useState } from "react";
import { FileText, Image as ImageIcon, Code, Maximize2 } from "lucide-react";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/Dialog";

interface MediaBlockProps {
  type: "image" | "pdf" | "code" | "file";
  url?: string;
  name?: string;
  size?: string;
}

export function MediaBlock({ type, url, name, size }: MediaBlockProps) {
  if (type === "image" && url) {
    return (
      <Dialog>
        <div className="relative group rounded-xl overflow-hidden border border-border inline-block max-w-sm cursor-zoom-in bg-white/5">
          <DialogTrigger asChild>
            <div className="relative">
              {/* Thumbnail rendering */}
              <img src={url} alt={name || "Image"} className="w-full h-auto object-cover max-h-48" loading="lazy" />
              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <Maximize2 className="text-white w-6 h-6" />
              </div>
            </div>
          </DialogTrigger>
        </div>
        <DialogContent className="max-w-4xl bg-transparent border-none shadow-none p-0">
          <img src={url} alt={name || "Image full size"} className="w-full h-auto rounded-lg object-contain" />
        </DialogContent>
      </Dialog>
    );
  }

  // Generic File / PDF / Code Preview
  return (
    <div className="flex items-center gap-3 p-3 rounded-xl border border-border bg-surface hover:bg-white/[0.02] transition-colors max-w-sm cursor-pointer group">
      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary/20 transition-colors">
        {type === "pdf" ? <FileText className="w-5 h-5" /> : type === "code" ? <Code className="w-5 h-5" /> : <ImageIcon className="w-5 h-5" />}
      </div>
      <div className="flex flex-col flex-1 min-w-0">
        <span className="text-sm font-medium text-text-primary truncate">{name || "Attached File"}</span>
        <span className="text-xs text-text-muted">{size || "Unknown size"} • {type.toUpperCase()}</span>
      </div>
    </div>
  );
}
