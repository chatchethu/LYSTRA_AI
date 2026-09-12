import React, { memo } from "react";
import clsx from "clsx";
import { MessageStatus } from "@/store/chatStore";
import { FileText, Image as ImageIcon, Video, Download } from "lucide-react";

interface UserMessageProps {
  content: string;
  status: MessageStatus;
  attachments?: string[];
  isGroupStart?: boolean;
  isGroupEnd?: boolean;
  onReply?: () => void;
}

export const UserMessage = memo(function UserMessage({ content, status, attachments, onReply }: UserMessageProps) {
  return (
    <div className="w-full flex justify-end">
      <div 
        className={clsx(
          "max-w-[80%] md:max-w-[70%] flex flex-col gap-2 transition-opacity duration-300",
          status === "pending" ? "opacity-70" : "opacity-100"
        )}
      >
        {attachments && attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 justify-end">
            {attachments.map((att, i) => {
              const isImage = /\.(jpg|jpeg|png|gif|webp)$/i.test(att);
              const isVideo = /\.(mp4|webm|ogg)$/i.test(att);
              
              if (isImage) {
                return (
                  <div key={i} className="relative group rounded-[var(--radius-md)] overflow-hidden border border-[var(--border-subtle)] shadow-[var(--shadow-subtle)] max-w-[200px]">
                    <img src={att} alt="attachment" className="w-full h-auto object-cover" loading="lazy" />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <a href={att} download className="p-2 bg-white/20 hover:bg-white/40 rounded-full text-white backdrop-blur-sm transition-colors">
                        <Download className="w-4 h-4" />
                      </a>
                    </div>
                  </div>
                );
              }
              
              if (isVideo) {
                return (
                  <div key={i} className="relative rounded-[var(--radius-md)] overflow-hidden border border-[var(--border-subtle)] shadow-[var(--shadow-subtle)] max-w-[250px]">
                    <video src={att} controls className="w-full h-auto" preload="metadata" />
                  </div>
                );
              }

              return (
                <div key={i} className="flex items-center gap-3 bg-[var(--bg-elevated)] border border-[var(--border-strong)] px-3 py-2 rounded-[var(--radius-md)] shadow-[var(--shadow-subtle)] hover:border-[var(--text-tertiary)] transition-colors cursor-pointer group">
                  <div className="p-2 bg-[var(--bg-surface)] rounded-md text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[13px] font-medium text-[var(--text-primary)] truncate max-w-[150px]">{att.split('/').pop()}</span>
                    <span className="text-[11px] text-[var(--text-tertiary)]">Document</span>
                  </div>
                  <a href={att} download className="ml-2 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors p-1">
                    <Download className="w-3.5 h-3.5" />
                  </a>
                </div>
              );
            })}
          </div>
        )}
        {content && (
          <div className="px-5 py-3 rounded-[var(--radius-lg)] rounded-tr-sm bg-[var(--accent-primary)] text-[var(--bg-base)] border-transparent shadow-[var(--shadow-subtle)] self-end whitespace-pre-wrap font-body text-[15px]">
            {content}
          </div>
        )}
      </div>
    </div>
  );
});
