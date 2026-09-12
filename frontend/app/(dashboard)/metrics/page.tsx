"use client";

import { useEffect, useState } from "react";
import { Activity, BarChart2, MessageSquare, RefreshCcw, ShieldAlert, GitMerge, Settings2, Hash } from "lucide-react";
import clsx from "clsx";
import { getFriendlyErrorMessage } from "@/lib/api/errors";

interface MetricsData {
  status: string;
  total_turns: number;
  conversations: number;
  topic_switches: number;
  quality_score: number;
  correction_rate_pct: number;
  flag_rate_pct: number;
  revision_rate_pct: number;
  avg_response_words: number;
  mode_distribution: Record<string, number>;
}

export default function MetricsPage() {
  const [data, setData] = useState<MetricsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { fetchApi } = await import("@/lib/api/client");
      const json = await fetchApi<MetricsData>("/api/v1/metrics");
      setData(json);
    } catch (err: any) {
      setError(getFriendlyErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    // Refresh every 30 seconds
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading && !data) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-[#0A0D14]">
        <div className="flex flex-col items-center gap-4 text-primary">
          <RefreshCcw className="w-8 h-8 animate-spin" />
          <p className="text-sm font-medium">Loading intelligence metrics...</p>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-[#0A0D14]">
        <div className="flex flex-col items-center gap-4 text-error">
          <ShieldAlert className="w-8 h-8" />
          <p className="text-sm font-medium">{error}</p>
          <button onClick={fetchMetrics} className="mt-2 px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition">Retry</button>
        </div>
      </div>
    );
  }

  if (!data || data.status === "no_data") {
    return (
      <div className="flex h-full w-full items-center justify-center bg-[#0A0D14]">
        <div className="text-center text-text-muted">
          <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <h2 className="text-xl font-semibold mb-2">No Data Available</h2>
          <p>Start a conversation to generate metrics.</p>
        </div>
      </div>
    );
  }

  const qualityColor = data.quality_score >= 80 ? "text-success drop-shadow-[0_0_8px_rgba(34,197,94,0.5)]" 
                     : data.quality_score >= 60 ? "text-warning drop-shadow-[0_0_8px_rgba(245,158,11,0.5)]" 
                     : "text-error drop-shadow-[0_0_8px_rgba(239,68,68,0.5)]";

  return (
    <div className="flex-1 overflow-y-auto bg-[#0A0D14] p-6 md:p-10 custom-scrollbar">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold gradient-text flex items-center gap-3">
              <Activity className="w-8 h-8 text-primary" />
              Intelligence Dashboard
            </h1>
            <p className="text-text-muted mt-2">Real-time conversation analytics and agent performance.</p>
          </div>
          <button 
            onClick={fetchMetrics}
            disabled={isLoading}
            className="p-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 text-text-secondary hover:text-text-primary transition-all disabled:opacity-50"
          >
            <RefreshCcw className={clsx("w-5 h-5", isLoading && "animate-spin")} />
          </button>
        </div>

        {/* Top Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="glass-dark border border-primary/30 p-6 rounded-2xl bg-primary/5 flex flex-col justify-between">
            <div className="flex items-center gap-2 text-primary font-medium text-sm mb-4 uppercase tracking-wider">
              <BarChart2 className="w-4 h-4" /> Quality Score
            </div>
            <div className={clsx("text-5xl font-bold", qualityColor)}>
              {data.quality_score}
            </div>
          </div>
          
          <div className="glass-dark border border-white/10 p-6 rounded-2xl flex flex-col justify-between">
            <div className="flex items-center gap-2 text-text-muted font-medium text-sm mb-4 uppercase tracking-wider">
              <MessageSquare className="w-4 h-4" /> Total Turns
            </div>
            <div className="text-4xl font-bold text-text-primary">
              {data.total_turns}
            </div>
          </div>

          <div className="glass-dark border border-white/10 p-6 rounded-2xl flex flex-col justify-between">
            <div className="flex items-center gap-2 text-text-muted font-medium text-sm mb-4 uppercase tracking-wider">
              <Hash className="w-4 h-4" /> Conversations
            </div>
            <div className="text-4xl font-bold text-text-primary">
              {data.conversations}
            </div>
          </div>

          <div className="glass-dark border border-white/10 p-6 rounded-2xl flex flex-col justify-between">
            <div className="flex items-center gap-2 text-text-muted font-medium text-sm mb-4 uppercase tracking-wider">
              <GitMerge className="w-4 h-4" /> Topic Switches
            </div>
            <div className="text-4xl font-bold text-text-primary">
              {data.topic_switches}
            </div>
          </div>
        </div>

        {/* Secondary Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="glass-dark border border-white/10 p-5 rounded-xl flex items-center justify-between">
            <div>
              <div className="text-xs text-text-muted uppercase tracking-wider mb-1 font-medium">Correction Rate</div>
              <div className="text-2xl font-bold text-text-primary">{data.correction_rate_pct}%</div>
            </div>
            <ShieldAlert className="w-8 h-8 text-warning/50" />
          </div>

          <div className="glass-dark border border-white/10 p-5 rounded-xl flex items-center justify-between">
            <div>
              <div className="text-xs text-text-muted uppercase tracking-wider mb-1 font-medium">Flag Rate</div>
              <div className="text-2xl font-bold text-text-primary">{data.flag_rate_pct}%</div>
            </div>
            <ShieldAlert className="w-8 h-8 text-error/50" />
          </div>

          <div className="glass-dark border border-white/10 p-5 rounded-xl flex items-center justify-between">
            <div>
              <div className="text-xs text-text-muted uppercase tracking-wider mb-1 font-medium">Revision Rate</div>
              <div className="text-2xl font-bold text-text-primary">{data.revision_rate_pct}%</div>
            </div>
            <Settings2 className="w-8 h-8 text-accent/50" />
          </div>
        </div>

        {/* Mode Distribution */}
        <div className="glass-dark border border-white/10 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-6 flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" /> Mode Distribution
          </h3>
          <div className="space-y-4">
            {Object.entries(data.mode_distribution).sort((a, b) => b[1] - a[1]).map(([mode, count]) => {
              const percentage = Math.round((count / data.total_turns) * 100) || 0;
              return (
                <div key={mode} className="flex items-center gap-4">
                  <div className="w-24 text-sm font-medium text-text-secondary uppercase">{mode}</div>
                  <div className="flex-1 h-3 bg-black/40 rounded-full overflow-hidden border border-white/5">
                    <div 
                      className="h-full bg-gradient-to-r from-primary to-accent transition-all duration-1000 ease-out rounded-full" 
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <div className="w-12 text-right text-sm font-bold text-text-primary">{count}</div>
                </div>
              );
            })}
          </div>
        </div>
        
      </div>
    </div>
  );
}

