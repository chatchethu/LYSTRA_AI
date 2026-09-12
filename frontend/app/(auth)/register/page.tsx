"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Brain, ArrowRight, Mail, Lock, User } from "lucide-react";
import clsx from "clsx";

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      router.push("/chat");
    }, 1000);
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-background">
      {/* Background animations */}
      <div className="absolute inset-0 z-0">
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[128px] animate-pulse-glow" />
        <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-accent/20 rounded-full blur-[128px] animate-pulse-glow" style={{ animationDelay: "1s" }} />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay" />
      </div>

      <div className="z-10 w-full max-w-md p-6">
        <div className="glass-card p-8 animate-slideUp">
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white mb-4 shadow-[0_0_24px_rgba(124,58,237,0.4)]">
              <Brain className="w-6 h-6" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Create Account</h1>
            <p className="text-text-muted text-sm text-center">Join your Personal AI workspace</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary ml-1">Full Name</label>
              <div className="relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-primary to-accent rounded-lg blur opacity-0 group-focus-within:opacity-30 transition duration-500"></div>
                <div className="relative flex items-center bg-black/40 border border-white/10 rounded-lg overflow-hidden">
                  <div className="pl-3 text-text-muted">
                    <User className="w-4 h-4" />
                  </div>
                  <input 
                    type="text" 
                    required
                    className="w-full bg-transparent px-3 py-2.5 text-sm focus:outline-none text-white placeholder:text-text-muted/50"
                    placeholder="John Doe"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary ml-1">Email</label>
              <div className="relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-primary to-accent rounded-lg blur opacity-0 group-focus-within:opacity-30 transition duration-500"></div>
                <div className="relative flex items-center bg-black/40 border border-white/10 rounded-lg overflow-hidden">
                  <div className="pl-3 text-text-muted">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input 
                    type="email" 
                    required
                    className="w-full bg-transparent px-3 py-2.5 text-sm focus:outline-none text-white placeholder:text-text-muted/50"
                    placeholder="you@example.com"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-text-secondary ml-1">Password</label>
              <div className="relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-primary to-accent rounded-lg blur opacity-0 group-focus-within:opacity-30 transition duration-500"></div>
                <div className="relative flex items-center bg-black/40 border border-white/10 rounded-lg overflow-hidden">
                  <div className="pl-3 text-text-muted">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input 
                    type="password" 
                    required
                    className="w-full bg-transparent px-3 py-2.5 text-sm focus:outline-none text-white placeholder:text-text-muted/50"
                    placeholder="••••••••"
                  />
                </div>
              </div>
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="w-full mt-6 bg-gradient-to-r from-primary to-accent hover:from-primary/90 hover:to-accent/90 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 transition-all hover:shadow-[0_0_20px_rgba(124,58,237,0.4)] disabled:opacity-70"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  Create Account
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-text-muted">
            Already have an account?{" "}
            <Link href="/login" className="text-primary hover:text-white transition-colors font-medium">
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
