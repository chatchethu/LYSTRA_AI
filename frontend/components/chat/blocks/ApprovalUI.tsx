import React from "react";
import { AlertTriangle, Check, X } from "lucide-react";

interface ApprovalUIProps {
  action: string;
  reason: string;
  onApprove?: () => void;
  onReject?: () => void;
  status?: "pending" | "approved" | "rejected";
}

export function ApprovalUI({ action, reason, onApprove, onReject, status = "pending" }: ApprovalUIProps) {
  return (
    <div className="w-full max-w-md bg-surface border border-warning/30 rounded-xl overflow-hidden shadow-sm">
      <div className="bg-warning/10 px-4 py-2.5 flex items-center gap-2 border-b border-warning/20">
        <AlertTriangle className="w-4 h-4 text-warning" />
        <span className="font-semibold text-warning text-sm tracking-wide">LYSTRA needs your approval</span>
      </div>
      
      <div className="p-4 flex flex-col gap-3">
        <div className="flex flex-col gap-1 text-sm">
          <span className="text-text-muted font-medium text-xs uppercase tracking-wider">Action</span>
          <span className="text-text-primary">{action}</span>
        </div>
        
        <div className="flex flex-col gap-1 text-sm">
          <span className="text-text-muted font-medium text-xs uppercase tracking-wider">Why</span>
          <span className="text-text-secondary leading-relaxed">{reason}</span>
        </div>

        {status === "pending" ? (
          <div className="flex items-center gap-3 mt-2">
            <button 
              onClick={onApprove}
              className="flex-1 bg-primary text-white py-2 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 hover:bg-primary/90 transition-colors"
            >
              <Check className="w-4 h-4" />
              Approve
            </button>
            <button 
              onClick={onReject}
              className="flex-1 bg-surface border border-border text-text-primary py-2 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 hover:bg-white/5 transition-colors"
            >
              <X className="w-4 h-4" />
              Reject
            </button>
          </div>
        ) : (
          <div className={`mt-2 py-2 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 ${status === "approved" ? "bg-success/10 text-success" : "bg-error/10 text-error"}`}>
            {status === "approved" ? (
              <><Check className="w-4 h-4" /> Approved</>
            ) : (
              <><X className="w-4 h-4" /> Rejected</>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
