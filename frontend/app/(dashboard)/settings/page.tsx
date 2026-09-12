"use client";

import { useState, useEffect } from "react";
import { User, Cpu, Database, Wrench, Mic, Palette, Key, Save } from "lucide-react";
import clsx from "clsx";
import { modelsClient } from "@/lib/api/models";
import { getFriendlyErrorMessage } from "@/lib/api/errors";
import { useToast } from "@/components/ui/ToastContext";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("ai");
  const [models, setModels] = useState<any[]>([]);
  const { showErrorToast, showToast } = useToast();
  const [settings, setSettings] = useState({
    default_model: "gpt-4-turbo",
    temperature: 0.7,
    personality: "helpful",
    response_style: "balanced",
    language: "en",
    proactivity_level: "medium",
    verbosity: 2
  });

  useEffect(() => {
    // Fetch settings
    import("@/lib/api/client").then(({ fetchApi }) => {
      fetchApi("/api/v1/settings")
        .then((res: any) => {
          if (res.settings) setSettings(res.settings);
        })
        .catch((error: unknown) => console.warn(error instanceof Error ? error.message : error));
    });

    // Fetch models
    modelsClient.list().then((data: any) => {
      let extracted = Array.isArray(data) ? data : (data?.models || []);
      if (!Array.isArray(extracted)) extracted = [];
      setModels(extracted);
    }).catch((err) => {
      console.warn("Failed to load models:", err?.message);
      showErrorToast(err);
      setModels([{ id: "gpt-4-turbo", name: "GPT-4 Turbo (Fallback)" }]);
    });
  }, [showErrorToast, showToast]);

  const updateSetting = async (key: string, value: string | number) => {
    const previous = { ...settings };
    const next = { ...settings, [key]: value };

    // Optimistic UI update
    setSettings(next);

    try {
      const { fetchApi } = await import("@/lib/api/client");
      await fetchApi("/api/v1/settings", {
        method: "POST",
        body: JSON.stringify({ [key]: value })
      });
      // Optionally show toast on success
      // showToast("Setting saved", "success");
    } catch (error) {
      console.warn(error instanceof Error ? error.message : error);
      // Rollback
      setSettings(previous);
      showErrorToast("Failed to save setting");
    }
  };

  const tabs = [
    { section: "Account", items: [
      { id: "profile", label: "Profile", icon: User },
      { id: "api", label: "Security Keys", icon: Key },
    ]},
    { section: "Preferences", items: [
      { id: "ai", label: "AI Settings", icon: Cpu },
      { id: "appearance", label: "Appearance", icon: Palette },
    ]},
    { section: "Advanced", items: [
      { id: "memory", label: "Memory Storage", icon: Database },
      { id: "tools", label: "Plugins Tools", icon: Wrench },
    ]}
  ];

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar flex bg-[var(--bg-base)]">
      {/* Settings Sidebar */}
      <div className="w-64 border-r border-[var(--border-subtle)] p-6 hidden md:block bg-[var(--bg-elevated)]">
        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6">Settings</h2>
        <nav className="space-y-6">
          {tabs.map((group, idx) => (
            <div key={idx} className="space-y-2">
              <div className="px-3 text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider">{group.section}</div>
              <div className="space-y-1">
                {group.items.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={clsx(
                      "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                      activeTab === tab.id
                        ? "bg-[var(--accent-primary)]/10 text-[var(--accent-primary)]"
                        : "text-[var(--text-secondary)] hover:bg-[var(--bg-surface)] hover:text-[var(--text-primary)]"
                    )}
                  >
                    <tab.icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </nav>
      </div>

      {/* Settings Content */}
      <div className="flex-1 p-6 md:p-10 max-w-3xl">
        {/* Mobile Nav */}
        <div className="md:hidden mb-8 overflow-x-auto hide-scrollbar flex gap-2">
          {tabs.flatMap(g => g.items).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors border",
                activeTab === tab.id
                  ? "bg-primary/20 text-primary border-primary/30"
                  : "bg-black/30 text-text-secondary border-white/5"
              )}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "ai" && (
          <div className="space-y-8 animate-fadeIn">
            <div>
              <h3 className="text-2xl font-bold text-white mb-2">AI Settings</h3>
              <p className="text-text-muted">Changes save automatically.</p>
            </div>

            <div className="glass-card p-6 space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-white">Default Model</label>
                <select
                  value={settings.default_model}
                  onChange={(e) => updateSetting("default_model", e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50"
                >
                  {!Array.isArray(models) || models.length === 0 ? (
                    <option value="">Loading models...</option>
                  ) : (
                    models.map((m) => (
                      <option key={m.id || m.name} value={m.id || m.name}>
                        {m.name || m.id}
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <label className="text-sm font-medium text-white">Temperature (Creativity)</label>
                  <span className="text-sm text-primary font-mono bg-primary/10 px-2 py-0.5 rounded">{settings.temperature}</span>
                </div>
                <input
                  type="range"
                  min="0" max="2" step="0.1"
                  value={settings.temperature}
                  onChange={(e) => updateSetting("temperature", parseFloat(e.target.value))}
                  className="w-full accent-primary"
                />
                <div className="flex justify-between text-xs text-text-muted">
                  <span>Precise</span>
                  <span>Creative</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-white">Personality</label>
                  <select
                    value={settings.personality}
                    onChange={(e) => updateSetting("personality", e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50"
                  >
                    <option value="helpful">Helpful & Professional</option>
                    <option value="casual">Casual & Friendly</option>
                    <option value="direct">Direct & Concise</option>
                    <option value="humorous">Humorous & Witty</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-white">Response Style</label>
                  <select
                    value={settings.response_style}
                    onChange={(e) => updateSetting("response_style", e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50"
                  >
                    <option value="balanced">Balanced</option>
                    <option value="analytical">Analytical</option>
                    <option value="creative">Creative</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-white">Language</label>
                  <select
                    value={settings.language}
                    onChange={(e) => updateSetting("language", e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50"
                  >
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="zh">Chinese</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-white">Proactivity Level</label>
                  <select
                    value={settings.proactivity_level}
                    onChange={(e) => updateSetting("proactivity_level", e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50"
                  >
                    <option value="low">Low (Wait for instructions)</option>
                    <option value="medium">Medium (Suggest improvements)</option>
                    <option value="high">High (Proactively take actions)</option>
                  </select>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <label className="text-sm font-medium text-white">Verbosity</label>
                  <span className="text-sm text-primary font-mono bg-primary/10 px-2 py-0.5 rounded">{settings.verbosity === 1 ? 'Concise' : settings.verbosity === 3 ? 'Detailed' : 'Medium'}</span>
                </div>
                <input
                  type="range" min="1" max="3" step="1"
                  value={settings.verbosity}
                  onChange={(e) => updateSetting("verbosity", parseInt(e.target.value))}
                  className="w-full accent-primary"
                />
                <div className="flex justify-between text-xs text-text-muted">
                  <span>Concise</span>
                  <span>Detailed</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab !== "ai" && (
          <div className="flex flex-col items-center justify-center h-64 glass-card p-6 border-dashed border-white/10">
            <Cpu className="w-12 h-12 text-text-muted mb-4 opacity-50" />
            <h3 className="text-lg font-medium text-text-secondary">Section under construction</h3>
            <p className="text-sm text-text-muted text-center mt-2 max-w-sm">
              The {tabs.flatMap(g => g.items).find(t => t.id === activeTab)?.label} settings are being updated. Check back soon.
            </p>
          </div>
        )}

      </div>
    </div>
  );
}

