"use client";

import { useState, useEffect } from "react";
import { BrainCircuit, Trash2, Plus, Sparkles, Filter, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";
import clsx from "clsx";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { memoryClient } from "@/lib/api/memory";
import { Memory } from "@/types/memory";
import { useToast } from "@/components/ui/ToastContext";

export default function BrainPage() {
  const { isAuthenticated } = useAuth();
  const { showErrorToast, showToast } = useToast();
  const [memories, setMemories] = useState<Memory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string | null>(null);
  
  const [newMemory, setNewMemory] = useState("");
  const [isAdding, setIsAdding] = useState(false);

  const fetchMemories = async () => {
    if (!isAuthenticated) return;
    setIsLoading(true);
    try {
      const data = await memoryClient.list(filter || undefined);
      setMemories(data);
    } catch (e) {
      console.error(e);
      showErrorToast(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, [isAuthenticated, filter]);

  const handleDelete = async (id: string) => {
    if (!confirm("Forget this memory forever?")) return;
    try {
      await memoryClient.delete(id);
      setMemories(prev => prev.filter(m => m.id !== id));
      showToast("Memory forgotten.", "success");
    } catch (e) {
      console.error(e);
      showErrorToast(e);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMemory.trim()) return;
    setIsAdding(true);
    try {
      const { fetchApi } = await import("@/lib/api/client");
      await fetchApi("/api/v1/memory", {
        method: "POST",
        body: JSON.stringify({
          content: newMemory,
          memory_type: "fact",
          importance: 0.8,
          source: "manual"
        })
      });
      setNewMemory("");
      showToast("Memory saved successfully.", "success");
      fetchMemories();
    } catch (e) {
      console.error(e);
      showErrorToast(e);
    } finally {
      setIsLoading(false);
      setIsAdding(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0A0D14] text-white">
      {/* Header */}
      <header className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-background/80 backdrop-blur-md sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <Link href="/chat" className="p-2 hover:bg-white/5 rounded-md text-text-muted hover:text-white transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="flex items-center gap-3">
            <div className="p-1.5 bg-primary/20 rounded-lg border border-primary/30 text-primary">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <h2 className="font-semibold text-text-primary text-lg tracking-wide">LYSTRA Brain</h2>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6 md:p-10 custom-scrollbar">
        <div className="max-w-5xl mx-auto">
          
          <div className="mb-10 text-center">
            <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary via-accent to-primary animate-gradient-x pb-2">
              Memory Matrix
            </h1>
            <p className="text-text-muted mt-2 max-w-xl mx-auto text-sm">
              LYSTRA autonomously learns your preferences, goals, and facts through conversation. Everything she knows about you is stored securely in vector space.
            </p>
          </div>

          {/* Add Memory Form */}
          <div className="bg-[#121620] border border-white/5 p-4 rounded-2xl shadow-xl mb-8 relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/10 to-accent/10 rounded-2xl blur opacity-20 group-focus-within:opacity-60 transition duration-500"></div>
            <form onSubmit={handleAdd} className="relative flex items-center gap-3">
              <div className="p-3 bg-white/5 rounded-xl text-text-muted">
                <Plus className="w-5 h-5" />
              </div>
              <input 
                type="text" 
                value={newMemory}
                onChange={(e) => setNewMemory(e.target.value)}
                placeholder="Teach LYSTRA a new fact about yourself..."
                className="flex-1 bg-transparent border-none focus:outline-none text-white placeholder:text-white/20 text-sm"
                disabled={isAdding}
              />
              <button 
                type="submit"
                disabled={!newMemory.trim() || isAdding}
                className={clsx(
                  "px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 flex items-center gap-2",
                  newMemory.trim() && !isAdding
                    ? "bg-primary text-white hover:bg-primary-light shadow-[0_4px_12px_rgba(124,58,237,0.3)]"
                    : "bg-white/5 text-text-muted cursor-not-allowed"
                )}
              >
                {isAdding ? "Injecting..." : "Memorize"}
              </button>
            </form>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-2 mb-8 justify-center">
            {['all', 'fact', 'preference', 'goal', 'decision'].map((type) => (
              <button
                key={type}
                onClick={() => setFilter(type === 'all' ? null : type)}
                className={clsx(
                  "px-4 py-1.5 rounded-full text-xs font-semibold capitalize transition-all duration-300 border",
                  (filter === type || (filter === null && type === 'all'))
                    ? "bg-primary/20 text-primary border-primary/30 shadow-[0_0_15px_rgba(124,58,237,0.15)]"
                    : "bg-transparent text-text-muted border-white/5 hover:border-white/10 hover:text-white"
                )}
              >
                {type}
              </button>
            ))}
          </div>

          {/* Memory Grid */}
          {isLoading ? (
            <div className="flex items-center justify-center py-20 text-primary">
              <BrainCircuit className="w-8 h-8 animate-pulse" />
            </div>
          ) : memories.length === 0 ? (
            <div className="text-center py-20">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/5 text-text-muted mb-4">
                <Sparkles className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-medium text-white">Tabula Rasa</h3>
              <p className="text-text-muted text-sm mt-2">LYSTRA hasn't learned any memories in this category yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {memories.map((mem) => (
                <div key={mem.id} className="bg-white/5 border border-white/5 rounded-2xl p-5 hover:bg-white/[0.07] hover:border-white/10 transition-all duration-300 group flex flex-col h-full relative overflow-hidden">
                  
                  <div className="flex items-center justify-between mb-3 relative z-10">
                    <span className={clsx(
                      "text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full",
                      mem.memory_type === 'preference' ? "bg-accent/10 text-accent border border-accent/20" :
                      mem.memory_type === 'goal' ? "bg-success/10 text-success border border-success/20" :
                      "bg-primary/10 text-primary border border-primary/20"
                    )}>
                      {mem.memory_type}
                    </span>
                    <button 
                      onClick={() => handleDelete(mem.id)}
                      className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-error/10 hover:text-error text-text-muted rounded-md transition-all"
                      title="Forget this memory"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <p className="text-white text-sm leading-relaxed flex-1 relative z-10">
                    "{mem.content}"
                  </p>
                  
                    <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between text-[10px] text-text-muted relative z-10">
                      <div className="flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3 text-success" />
                        Conf: {((mem.importance || 0.8) * 100).toFixed(0)}%
                      </div>
                      <div>Source: {mem.source || 'inferred'}</div>
                    </div>
                  
                  {/* Subtle background glow */}
                  <div className={clsx(
                    "absolute -bottom-10 -right-10 w-32 h-32 blur-3xl rounded-full opacity-10 pointer-events-none transition-opacity group-hover:opacity-20",
                    mem.memory_type === 'preference' ? "bg-accent" :
                    mem.memory_type === 'goal' ? "bg-success" :
                    "bg-primary"
                  )}></div>
                </div>
              ))}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

