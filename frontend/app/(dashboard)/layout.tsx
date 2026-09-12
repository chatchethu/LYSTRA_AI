"use client";

import { AppShell } from "@/components/layout/AppShell";
import { useEffect } from "react";
import { useChatStore } from "@/store/chatStore";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const setConversationId = useChatStore((state) => state.setConversationId);

  // Expose global nav functions for backwards compat temporarily
  useEffect(() => {
    (window as any).__setGlobalConversationId = setConversationId;
  }, [setConversationId]);

  return (
    <AppShell>
      {children}
    </AppShell>
  );
}
