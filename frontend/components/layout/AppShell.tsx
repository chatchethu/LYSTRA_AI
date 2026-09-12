"use client";

import { ReactNode, useState, useEffect } from "react";
import { Sidebar } from "./Sidebar";
import { Menu, X } from "lucide-react";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { ConnectionBanner } from "./ConnectionBanner";
import { AuthModal } from "@/components/auth/AuthModal";

export function AppShell({ children }: { children: ReactNode }) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);

  useEffect(() => {
    const handleShowAuth = () => setShowAuthModal(true);
    window.addEventListener("show-auth-modal", handleShowAuth);
    return () => window.removeEventListener("show-auth-modal", handleShowAuth);
  }, []);

  // Close mobile menu on route change or when resizing to desktop
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setIsMobileMenuOpen(false);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div className="flex h-screen bg-[var(--bg-base)] overflow-hidden text-[var(--text-primary)] relative">
      <ConnectionBanner />
      
      {/* Mobile Header / Safe Area */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-14 bg-[var(--bg-surface)]/80 backdrop-blur-md border-b border-[var(--border-subtle)] flex items-center justify-between px-4 z-40 pb-[env(safe-area-inset-top)]">
        <div className="flex items-center gap-2">
          <div className="font-heading text-lg font-bold">LYSTRA</div>
        </div>
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 -mr-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          aria-label="Toggle Menu"
        >
          {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Sidebar - Desktop (Fixed) & Mobile (Drawer) */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-sidebar bg-[var(--bg-surface)] border-r border-[var(--border-subtle)] transform transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0 ${
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <ErrorBoundary>
          <Sidebar onCloseMobile={() => setIsMobileMenuOpen(false)} />
        </ErrorBoundary>
      </div>

      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-full w-full max-w-full overflow-hidden relative lg:pt-0 pt-14">
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </main>

      {showAuthModal && (
        <AuthModal onClose={() => setShowAuthModal(false)} />
      )}
    </div>
  );
}
