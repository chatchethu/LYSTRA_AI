import React, { useEffect } from "react";
import { WifiOff, RefreshCw } from "lucide-react";
import { useChatStore } from "@/store/chatStore";
import { motion, AnimatePresence } from "framer-motion";

export function ConnectionBanner() {
  const connectionState = useChatStore(state => state.connectionState);
  const setConnectionState = useChatStore(state => state.setConnectionState);

  // Monitor native browser online/offline status
  useEffect(() => {
    if (typeof navigator !== "undefined") {
      setConnectionState(navigator.onLine ? "connected" : "disconnected");
    }

    const handleOnline = () => setConnectionState("connected");
    const handleOffline = () => setConnectionState("disconnected");

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [setConnectionState]);

  return (
    <AnimatePresence>
      {connectionState === "disconnected" && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
          className="fixed top-0 left-0 right-0 z-50 flex justify-center pt-2 pointer-events-none"
        >
          <div className="bg-error/90 text-white backdrop-blur-md px-4 py-2 rounded-full shadow-lg shadow-error/20 border border-error/50 flex items-center gap-2 pointer-events-auto">
            <WifiOff className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wider">Connection Lost</span>
            <span className="text-xs opacity-80 border-l border-white/20 pl-2 ml-1 flex items-center gap-1.5">
              <RefreshCw className="w-3 h-3 animate-spin" /> Reconnecting...
            </span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
