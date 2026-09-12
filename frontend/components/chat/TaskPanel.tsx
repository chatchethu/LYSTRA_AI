import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Square, Loader2, Sparkles, X } from "lucide-react";
import { useChatStore } from "@/store/chatStore";

export function TaskPanel() {
  const activeTask = useChatStore(state => state.activeTask);
  const setActiveTask = useChatStore(state => state.setActiveTask);

  if (!activeTask) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.95 }}
        transition={{ duration: 0.2 }}
        className="absolute top-16 left-1/2 -translate-x-1/2 z-40 w-full max-w-lg"
      >
        <div className="mx-4 bg-surface/95 backdrop-blur-xl border border-primary/20 rounded-xl shadow-2xl overflow-hidden shadow-primary/5">
          <div className="bg-primary/10 px-4 py-2.5 flex items-center justify-between border-b border-primary/10">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary" />
              <span className="font-semibold text-primary text-xs uppercase tracking-wider">Active Agent Task</span>
            </div>
            <button onClick={() => setActiveTask(null)} className="text-text-muted hover:text-text-primary transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
          
          <div className="p-4 flex flex-col gap-4">
            <div className="flex flex-col gap-1">
              <span className="text-xs text-text-muted font-medium">Goal</span>
              <span className="text-sm text-text-primary leading-tight">{activeTask.goal || "Processing requested task..."}</span>
            </div>

            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-text-muted font-medium">Progress</span>
                <span className="text-primary font-medium">{Math.round((activeTask.step / (activeTask.totalSteps || 1)) * 100)}%</span>
              </div>
              <div className="h-1.5 w-full bg-black/40 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary transition-all duration-500 ease-out" 
                  style={{ width: `${Math.max(5, (activeTask.step / (activeTask.totalSteps || 1)) * 100)}%` }} 
                />
              </div>
            </div>

            <div className="flex items-center justify-between bg-black/20 p-2.5 rounded-lg border border-white/5">
              <div className="flex items-center gap-2.5 min-w-0">
                <Loader2 className="w-4 h-4 text-primary animate-spin shrink-0" />
                <span className="text-xs text-text-primary truncate">{activeTask.currentAction || "Analyzing..."}</span>
              </div>
              
              <div className="flex items-center gap-1 shrink-0 ml-2">
                <button className="p-1.5 bg-white/5 hover:bg-white/10 rounded-md text-text-primary transition-colors" title="Pause Task">
                  <Play className="w-3.5 h-3.5" />
                </button>
                <button className="p-1.5 bg-error/10 hover:bg-error/20 rounded-md text-error transition-colors" title="Cancel Task">
                  <Square className="w-3.5 h-3.5" fill="currentColor" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
