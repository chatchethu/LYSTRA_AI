import React, { useState } from "react";
import { ListTodo, CheckCircle2, Circle, ArrowRight, ChevronDown, ChevronRight } from "lucide-react";
import clsx from "clsx";

interface PlanStep {
  title: string;
  status: "pending" | "active" | "completed";
}

export function PlanUI({ steps }: { steps: PlanStep[] }) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!steps || steps.length === 0) return null;

  const completedCount = steps.filter(s => s.status === "completed").length;
  const isAllDone = completedCount === steps.length;

  return (
    <div className="flex flex-col w-full max-w-sm rounded-xl border border-border bg-surface overflow-hidden shadow-sm">
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full p-3 bg-white/5 hover:bg-white/[0.07] transition-colors text-sm font-medium text-text-primary"
      >
        <div className="flex items-center gap-2">
          <ListTodo className="w-4 h-4 text-primary" />
          <span>{isAllDone ? "Plan completed" : "LYSTRA is working on this"}</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-black/20 text-text-muted">
            {completedCount}/{steps.length}
          </span>
        </div>
        {isExpanded ? <ChevronDown className="w-4 h-4 text-text-muted" /> : <ChevronRight className="w-4 h-4 text-text-muted" />}
      </button>

      {isExpanded && (
        <div className="flex flex-col gap-3 p-4 bg-transparent border-t border-border">
          {steps.map((step, idx) => (
            <div key={idx} className="flex items-start gap-3">
              <div className="mt-0.5">
                {step.status === "completed" ? (
                  <CheckCircle2 className="w-4 h-4 text-success" />
                ) : step.status === "active" ? (
                  <ArrowRight className="w-4 h-4 text-accent animate-pulse" />
                ) : (
                  <Circle className="w-4 h-4 text-text-muted/30" />
                )}
              </div>
              <span className={clsx(
                "text-sm leading-tight",
                step.status === "completed" ? "text-text-muted line-through opacity-70" :
                step.status === "active" ? "text-text-primary font-medium" : "text-text-muted"
              )}>
                {step.title}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
