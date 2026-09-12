"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, useRef } from "react";
import {
  Brain,
  Plus,
  Search,
  Trash2,
  MessageSquare,
  Settings,
  Activity,
  BrainCircuit,
  LogOut,
  LogIn,
  MoreVertical,
  Pencil,
  Archive,
} from "lucide-react";
import clsx from "clsx";
import { useAuth } from "@/components/auth/AuthProvider";
import { useChatStore } from "@/store/chatStore";
import { useDebounce } from "@/hooks/useDebounce";
import { Skeleton } from "@/components/ui/Skeleton";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from "@/components/ui/DropdownMenu";
import { Dialog, DialogContent, DialogTrigger, DialogClose } from "@/components/ui/Dialog";

import { Conversation } from "@/types/chat";

interface SidebarProps {
  onCloseMobile?: () => void;
}

export function Sidebar({ onCloseMobile }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, user, logout } = useAuth();

  const currentConversationId = useChatStore(state => state.conversationId);
  const setConversationId = useChatStore(state => state.setConversationId);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoadingConvs, setIsLoadingConvs] = useState(false);
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Phase 12: Search Keyboard Navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const fetchConversations = async () => {
    if (!isAuthenticated) return;
    setIsLoadingConvs(true);
    try {
      const { conversationsClient } = await import("@/lib/api/conversations");
      const data = await conversationsClient.list();
      setConversations(data);
    } catch (e: any) {
      if (e.status === 401) {
        logout();
      }
      console.warn("Failed to fetch conversations:", e?.message);
    } finally {
      setIsLoadingConvs(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) {
      setConversations([]);
      return;
    }
    fetchConversations();
  }, [isAuthenticated, currentConversationId]);

  // Listen for explicit refresh requests (e.g. after a new message is sent)
  useEffect(() => {
    const handler = () => fetchConversations();
    window.addEventListener("lystra-refresh-conversations", handler);
    return () => window.removeEventListener("lystra-refresh-conversations", handler);
  }, [isAuthenticated]);

  const handleNewChat = () => {
    setConversationId(null);
    if (pathname !== "/chat") router.push("/chat");
    if (onCloseMobile) onCloseMobile();
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Delete this conversation?")) return;
    try {
      const { conversationsClient } = await import("@/lib/api/conversations");
      await conversationsClient.delete(id);
      if (currentConversationId === id) setConversationId(null);
      else fetchConversations();
    } catch (error) {
      console.warn(error instanceof Error ? error.message : error);
    }
  };

  const filteredConvs = conversations.filter(c =>
    (c.title || "New Conversation").toLowerCase().includes(debouncedSearchQuery.toLowerCase())
  );

  const userInitials = user?.username?.slice(0, 2).toUpperCase() || user?.email?.slice(0, 2).toUpperCase() || "N";

  return (
    <aside className="w-[260px] h-screen bg-[#0f0f0f] flex flex-col border-r border-white/[0.06] shrink-0 relative z-20">
      {/* Logo */}
      <div className="p-4 flex items-center gap-2.5 border-b border-white/[0.06]">
        <span className="text-base font-bold tracking-tight text-white leading-none">LYSTRA</span>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center gap-2 px-3 py-2 bg-white/[0.05] hover:bg-white/[0.09] rounded-lg text-sm font-medium text-white/80 hover:text-white transition-all border border-white/[0.06] group"
        >
          <Plus className="w-4 h-4 text-primary group-hover:rotate-90 transition-transform duration-300" />
          New Chat
          <span className="ml-auto text-[10px] text-white/20">Ctrl+N</span>
        </button>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto px-3 pb-2 flex flex-col gap-1 custom-scrollbar">
        {isAuthenticated && (
          <>
            {/* Search */}
            <div className="relative mb-2">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30" />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search (Ctrl+K)..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full bg-white/[0.04] border border-white/[0.06] rounded-[var(--radius-md)] pl-8 pr-3 py-1.5 text-xs focus:outline-none focus:border-primary/40 transition-colors placeholder:text-[var(--text-tertiary)] text-[var(--text-primary)]"
              />
            </div>

            {/* Conversations List */}
            {isLoadingConvs ? (
              <div className="flex flex-col gap-2 py-2">
                <Skeleton className="h-9 w-full rounded-lg" />
                <Skeleton className="h-9 w-full rounded-lg opacity-80" />
                <Skeleton className="h-9 w-full rounded-lg opacity-60" />
                <Skeleton className="h-9 w-full rounded-lg opacity-40" />
              </div>
            ) : filteredConvs.length === 0 ? (
              <div className="text-center py-6">
                <MessageSquare className="w-6 h-6 text-white/20 mx-auto mb-2" />
                <p className="text-xs text-[var(--text-secondary)] font-medium">
                  {searchQuery ? "No messages found" : "No conversations yet"}
                </p>
              </div>
            ) : (
              <>
                {(() => {
                  const groups: Record<string, typeof filteredConvs> = {
                    "Today": [],
                    "Yesterday": [],
                    "Previous 7 Days": [],
                    "Older": []
                  };

                  const now = new Date();
                  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
                  const yesterday = today - 86400000;
                  const lastWeek = today - (7 * 86400000);

                  filteredConvs.forEach(conv => {
                    const date = new Date(conv.updated_at || conv.created_at || Date.now()).getTime();
                    if (date >= today) groups["Today"].push(conv);
                    else if (date >= yesterday) groups["Yesterday"].push(conv);
                    else if (date >= lastWeek) groups["Previous 7 Days"].push(conv);
                    else groups["Older"].push(conv);
                  });

                  return Object.entries(groups).map(([label, convs]) => {
                    if (convs.length === 0) return null;
                    return (
                      <div key={label} className="mb-3">
                        <p className="text-[10px] font-semibold uppercase tracking-widest text-white/20 px-2 mb-1.5">{label}</p>
                        <div className="flex flex-col gap-0.5">
                          {convs.map(conv => (
                            <Dialog key={conv.id}>
                              <div
                                onClick={() => {
                                  setConversationId(conv.id);
                                  if (pathname !== "/chat") router.push("/chat");
                                  if (onCloseMobile) onCloseMobile();
                                }}
                                className={clsx(
                                  "group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-all text-sm relative",
                                  currentConversationId === conv.id
                                    ? "bg-primary/10 text-white border border-primary/20"
                                    : "text-white/50 hover:bg-white/[0.05] hover:text-white/80"
                                )}
                              >
                                <div className="flex items-center gap-2 overflow-hidden min-w-0 flex-1">
                                  <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 opacity-50" />
                                  <span className="truncate text-xs">{conv.title || "New Conversation"}</span>
                                </div>

                                <div onClick={(e) => e.stopPropagation()} className="opacity-0 group-hover:opacity-100 transition-opacity">
                                  <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                      <button className="p-1 hover:bg-white/10 rounded-md text-text-muted hover:text-[var(--text-primary)] transition-colors">
                                        <MoreVertical className="w-3.5 h-3.5" />
                                      </button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end" className="w-40">
                                      <DropdownMenuItem>
                                        <Pencil className="w-3.5 h-3.5 mr-2" />
                                        Rename
                                      </DropdownMenuItem>
                                      <DropdownMenuItem>
                                        <Archive className="w-3.5 h-3.5 mr-2" />
                                        Archive
                                      </DropdownMenuItem>
                                      <DropdownMenuSeparator />
                                      <DialogTrigger asChild>
                                        <DropdownMenuItem className="text-error focus:text-error focus:bg-error/10">
                                          <Trash2 className="w-3.5 h-3.5 mr-2" />
                                          Delete
                                        </DropdownMenuItem>
                                      </DialogTrigger>
                                    </DropdownMenuContent>
                                  </DropdownMenu>
                                </div>
                              </div>
                              <DialogContent title="Delete Conversation" description={`Are you sure you want to delete "${conv.title || "New Conversation"}"?`}>
                                <div className="flex justify-end gap-2 mt-4">
                                  <DialogClose asChild>
                                    <button className="px-4 py-2 rounded-lg text-sm font-medium hover:bg-[var(--bg-elevated)] transition-colors">Cancel</button>
                                  </DialogClose>
                                  <DialogClose asChild>
                                    <button
                                      onClick={(e) => handleDelete(conv.id, e as any)}
                                      className="px-4 py-2 rounded-lg text-sm font-medium bg-error text-white hover:bg-error/90 transition-colors"
                                    >
                                      Delete
                                    </button>
                                  </DialogClose>
                                </div>
                              </DialogContent>
                            </Dialog>
                          ))}
                        </div>
                      </div>
                    );
                  });
                })()}
              </>
            )}
          </>
        )}

        {!isAuthenticated && (
          <div className="text-center py-8 px-2">
            <MessageSquare className="w-8 h-8 text-white/20 mx-auto mb-3" />
            <p className="text-xs text-white/50 font-medium leading-relaxed">Sign in to save and view your chat history</p>
          </div>
        )}
      </div>

      {/* Bottom Nav Links */}
      <div className="border-t border-white/[0.06] p-3 space-y-1">
        <Link href="/brain" className={clsx(
          "flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all",
          pathname.startsWith("/brain") ? "bg-primary/10 text-primary" : "text-white/40 hover:text-white/70 hover:bg-white/[0.04]"
        )}>
          <BrainCircuit className="w-4 h-4" />
          LYSTRA Brain
        </Link>
        <Link href="/metrics" className={clsx(
          "flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all",
          pathname.startsWith("/metrics") ? "bg-primary/10 text-primary" : "text-white/40 hover:text-white/70 hover:bg-white/[0.04]"
        )}>
          <Activity className="w-4 h-4" />
          Metrics
        </Link>
        <Link href="/settings" className={clsx(
          "flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all",
          pathname.startsWith("/settings") ? "bg-primary/10 text-primary" : "text-white/40 hover:text-white/70 hover:bg-white/[0.04]"
        )}>
          <Settings className="w-4 h-4" />
          Settings
        </Link>
      </div>

      {/* User Profile Footer */}
      <div className="border-t border-white/[0.06] p-3">
        {isAuthenticated && user ? (
          <div className="flex items-center gap-2.5 px-2 py-1.5 rounded-lg hover:bg-white/[0.04] transition-colors group">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary to-violet-500 flex items-center justify-center text-white font-bold text-xs flex-shrink-0">
              {userInitials}
            </div>
            <div className="flex flex-col min-w-0 flex-1">
              <span className="text-xs font-semibold text-white/80 truncate">{user.username || user.email}</span>
              <span className="text-[10px] text-white/30">Pro Account</span>
            </div>
            <button
              onClick={logout}
              title="Logout"
              className="opacity-0 group-hover:opacity-100 p-1 text-white/30 hover:text-red-400 transition-all"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => window.dispatchEvent(new Event("show-auth-modal"))}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-white/40 hover:text-white/70 hover:bg-white/[0.04] transition-all"
          >
            <LogIn className="w-4 h-4" />
            Sign In
          </button>
        )}
      </div>
    </aside>
  );
}
