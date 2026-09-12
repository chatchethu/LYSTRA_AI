"use client";

import { useState, useRef } from "react";
import { X, FileText, Image as ImageIcon, Loader2, CheckCircle, AlertCircle, Paperclip } from "lucide-react";

export interface AttachedFile {
  file_id: string;
  filename: string;
  type: "image" | "pdf" | "document";
  status: "uploading" | "ready" | "failed";
  page_count?: number;
  error?: string;
}

interface FileAttachmentProps {
  file: AttachedFile;
  onRemove: () => void;
}

const FILE_ICONS = {
  image: <ImageIcon className="w-3.5 h-3.5" />,
  pdf: <FileText className="w-3.5 h-3.5" />,
  document: <FileText className="w-3.5 h-3.5" />,
};

const FILE_EMOJIS = {
  image: "🖼️",
  pdf: "📄",
  document: "📝",
};

export function FileAttachment({ file, onRemove }: FileAttachmentProps) {
  const isUploading = file.status === "uploading";
  const isReady = file.status === "ready";
  const isFailed = file.status === "failed";

  return (
    <div
      className={`
        flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium
        border transition-all duration-200 max-w-xs
        ${isReady ? "bg-white/[0.06] border-white/[0.1] text-white/80" : ""}
        ${isUploading ? "bg-blue-500/10 border-blue-500/20 text-blue-300" : ""}
        ${isFailed ? "bg-red-500/10 border-red-500/20 text-red-400" : ""}
      `}
    >
      <span className="text-sm">{FILE_EMOJIS[file.type] ?? "📎"}</span>
      <span className="truncate max-w-[140px]">{file.filename}</span>

      {isUploading && (
        <Loader2 className="w-3 h-3 animate-spin text-blue-400 ml-1 flex-shrink-0" />
      )}
      {isReady && file.page_count && (
        <span className="text-white/30 flex-shrink-0">{file.page_count}p</span>
      )}
      {isReady && !file.page_count && (
        <CheckCircle className="w-3 h-3 text-green-400 ml-1 flex-shrink-0" />
      )}
      {isFailed && (
        <span title={file.error} className="ml-1 flex-shrink-0 flex items-center">
          <AlertCircle className="w-3 h-3 text-red-400" />
        </span>
      )}

      <button
        onClick={onRemove}
        className="ml-1 text-white/30 hover:text-white/70 transition-colors flex-shrink-0"
        title="Remove file"
      >
        <X className="w-3 h-3" />
      </button>
    </div>
  );
}

interface FilePickerProps {
  onFileAttached: (file: AttachedFile) => void;
  disabled?: boolean;
}

const ALLOWED_TYPES = [
  "image/jpeg", "image/jpg", "image/png", "image/webp",
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/msword",
];
const ALLOWED_EXT = ".jpg,.jpeg,.png,.webp,.pdf,.doc,.docx";

export function FilePicker({ onFileAttached, disabled }: FilePickerProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset input so same file can be re-selected
    e.target.value = "";

    // Validate on client before uploading
    if (!ALLOWED_TYPES.includes(file.type) && file.type !== "") {
      alert(`Unsupported file type. Allowed: JPG, PNG, WEBP, PDF, DOC, DOCX`);
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      alert("File is too large. Maximum is 50 MB.");
      return;
    }

    // Optimistic UI — show uploading state immediately
    const tempId = `temp-${Date.now()}`;
    const fileType: AttachedFile["type"] =
      file.type.startsWith("image/") ? "image" :
      file.type === "application/pdf" ? "pdf" : "document";

    onFileAttached({
      file_id: tempId,
      filename: file.name,
      type: fileType,
      status: "uploading",
    });

    try {
      const formData = new FormData();
      formData.append("file", file);
      const { filesClient } = await import("@/lib/api/files");
      const res = await filesClient.upload(formData) as any;

      onFileAttached({
        file_id: res.file_id,
        filename: res.filename,
        type: res.type as AttachedFile["type"],
        status: res.status === "ready" ? "ready" : res.status === "failed" ? "failed" : "uploading",
        page_count: res.page_count ?? undefined,
        error: res.error ?? undefined,
      });
    } catch (err: any) {
      onFileAttached({
        file_id: tempId,
        filename: file.name,
        type: fileType,
        status: "failed",
        error: err.data?.detail || "Network error — could not upload file",
      });
    }
  };

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept={ALLOWED_EXT}
        className="hidden"
        onChange={handleFile}
        disabled={disabled}
      />
      <button
        onClick={() => inputRef.current?.click()}
        disabled={disabled}
        className="p-2 text-white/25 hover:text-white/60 transition-colors rounded-lg hover:bg-white/[0.05] disabled:opacity-40 disabled:cursor-not-allowed"
        title="Attach a file (image, PDF, or Word document)"
      >
        <Paperclip className="w-4 h-4" />
      </button>
    </>
  );
}
