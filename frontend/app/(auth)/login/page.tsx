"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Brain, ArrowRight, Mail, Lock, AlertCircle } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
        credentials: "include",
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Incorrect email or password");
      }

      const data = await res.json();
      login(data.user);
      router.push("/chat");
    } catch (err: any) {
      setError(err.message || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-background">
      <div className="absolute inset-0 z-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[128px] animate-pulse-glow" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/20 rounded-full blur-[128px] animate-pulse-glow" style={{ animationDelay: "1s" }} />
      </div>
      <div className="z-10 w-full max-w-md p-6">
        <div className="glass-card p-8 animate-slideUp">
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white mb-4 shadow-[0_0_24px_rgba(124,58,237,0.4)]">
              <Brain className="w-6 h-6" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Welcome Back</h1>
            <p className="text-text-muted text-sm text-center">Sign in to continue to your Personal AI workspace</p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary ml-1">Email</label>
              <div className="flex items-center bg-black/40 border border-white/10 rounded-lg overflow-hidden">
                <div className="pl-3 text-text-muted"><Mail className="w-4 h-4" /></div>
                <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
                  className="w-full bg-transparent px-3 py-2.5 text-sm focus:outline-none text-white placeholder:text-text-muted/50"
                  placeholder="you@example.com" />
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary ml-1">Password</label>
              <div className="flex items-center bg-black/40 border border-white/10 rounded-lg overflow-hidden">
                <div className="pl-3 text-text-muted"><Lock className="w-4 h-4" /></div>
                <input type="password" required value={password} onChange={e => setPassword(e.target.value)}
                  className="w-full bg-transparent px-3 py-2.5 text-sm focus:outline-none text-white placeholder:text-text-muted/50"
                  placeholder="••••••••" />
              </div>
            </div>
            <button type="submit" disabled={loading}
              className="w-full mt-6 bg-gradient-to-r from-primary to-accent text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 transition-all disabled:opacity-70">
              {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <>Sign In <ArrowRight className="w-4 h-4" /></>}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-text-muted">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="text-primary hover:text-white transition-colors font-medium">Create one</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
