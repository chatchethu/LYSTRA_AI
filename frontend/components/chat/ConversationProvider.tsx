"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

interface ConvContextType {
  conversationId: string | null;
  setConversationId: (id: string | null) => void;
}

const ConvContext = createContext<ConvContextType>({
  conversationId: null,
  setConversationId: () => {},
});

export function ConversationProvider({ children }: { children: React.ReactNode }) {
  const [conversationId, setConversationIdState] = useState<string | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem("nova_active_conv");
    if (stored) setConversationIdState(stored);
  }, []);

  const setConversationId = (id: string | null) => {
    setConversationIdState(id);
    if (id) {
      localStorage.setItem("nova_active_conv", id);
    } else {
      localStorage.removeItem("nova_active_conv");
    }
  };

  return (
    <ConvContext.Provider value={{ conversationId, setConversationId }}>
      {children}
    </ConvContext.Provider>
  );
}

export function useConversation() {
  return useContext(ConvContext);
}
