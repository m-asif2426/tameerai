/* eslint-disable @next/next/no-img-element */
"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { useLanguage } from "@/contexts/LanguageContext";
import { apiClient, ApiUser } from "@/services/apiClient";
import { chatService, BackendChatSession } from "@/services/chatService";
import {
  LayoutDashboard,
  FolderOpen,
  MessageSquare,
  ShieldCheck,
  ShieldAlert,
  Scale,
  FileText,
  TrendingUp,
  BarChart3,
  ClipboardCheck,
  Settings,
  LogOut,
  Sun,
  Moon,
  Globe,
  Menu,
  X,
  Bell,
  Search,
  Plus,
  Pencil,
  Archive,
  Check,
  ChevronDown,
  ChevronRight,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  en: string;
  ur: string;
  badge?: string;
}

const engineeringNavItems: NavItem[] = [
  { href: "/dashboard", icon: LayoutDashboard, en: "Dashboard", ur: "ڈیش بورڈ" },
  { href: "/dashboard/projects", icon: FolderOpen, en: "Projects", ur: "منصوبے" },
  { href: "/dashboard/costs", icon: TrendingUp, en: "Cost Intelligence", ur: "لاگت انٹیلی جنس" },
  {
    href: "/dashboard/safety",
    icon: ShieldAlert,
    en: "Structural Safety",
    ur: "سٹرکچرل سیفٹی",
    badge: "38 Rules",
  },
  { href: "/dashboard/regulations", icon: Scale, en: "Regulations", ur: "عمارتی ضوابط" },
  { href: "/dashboard/compliance", icon: ShieldCheck, en: "Compliance Check", ur: "تعمیل کی جانچ" },
  { href: "/dashboard/contracts", icon: FileText, en: "Contract Analyzer", ur: "معاہدہ تجزیہ کار" },
  { href: "/dashboard/audit", icon: ClipboardCheck, en: "Audit & Inspection", ur: "آڈٹ اور معائنہ" },
  { href: "/dashboard/reports", icon: BarChart3, en: "Reports", ur: "رپورٹس" },
];

interface SessionGroup {
  id: "today" | "yesterday" | "week" | "older";
  labelEn: string;
  labelUr: string;
  items: BackendChatSession[];
}

function groupSessions(sessions: BackendChatSession[], searchQuery: string): SessionGroup[] {
  const filtered = sessions.filter((s) => {
    if (s.isArchived) return false;
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (s.title && s.title.toLowerCase().includes(q)) ||
      (s.preview && s.preview.toLowerCase().includes(q))
    );
  });

  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const yesterdayStart = todayStart - 86400000;
  const sevenDaysAgo = todayStart - 7 * 86400000;

  const todayList: BackendChatSession[] = [];
  const yesterdayList: BackendChatSession[] = [];
  const weekList: BackendChatSession[] = [];
  const olderList: BackendChatSession[] = [];

  for (const s of filtered) {
    const rawTime = s.updatedAt || s.createdAt || s.lastActivityAt;
    const time = rawTime ? new Date(rawTime).getTime() : 0;

    if (time >= todayStart) {
      todayList.push(s);
    } else if (time >= yesterdayStart) {
      yesterdayList.push(s);
    } else if (time >= sevenDaysAgo) {
      weekList.push(s);
    } else {
      olderList.push(s);
    }
  }

  const groups: SessionGroup[] = [];
  if (todayList.length > 0) groups.push({ id: "today", labelEn: "Today", labelUr: "آج", items: todayList });
  if (yesterdayList.length > 0) groups.push({ id: "yesterday", labelEn: "Yesterday", labelUr: "کل", items: yesterdayList });
  if (weekList.length > 0) groups.push({ id: "week", labelEn: "Previous 7 Days", labelUr: "گزشتہ 7 دن", items: weekList });
  if (olderList.length > 0) groups.push({ id: "older", labelEn: "Older", labelUr: "پرانی مشاورتیں", items: olderList });

  return groups;
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [toolsCollapsed, setToolsCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchSessionQuery, setSearchSessionQuery] = useState("");

  const [currentUser, setCurrentUser] = useState<ApiUser | null>(() => apiClient.getCachedUser());
  const [sessions, setSessions] = useState<BackendChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");

  // Sync activeSessionId with URL query params
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const sid = params.get("session");
    if (sid) {
      setActiveSessionId(sid);
    }
  }, [pathname]);

  // Session restoration and User Profile initialization
  useEffect(() => {
    const initializeSession = async () => {
      try {
        if (!apiClient.getToken()) {
          await apiClient.restoreSession();
        }
        const user = await apiClient.get<ApiUser>("/users/me");
        if (user) {
          setCurrentUser(user);
          apiClient.setCachedUser(user);
        }
      } catch (err: unknown) {
        console.warn("[DashboardLayout] Session initialization:", err instanceof Error ? err.message : String(err));
      }
    };

    initializeSession();
  }, []);

  // Fetch recent consultations on mount
  useEffect(() => {
    const loadSessions = async () => {
      try {
        const fetched = await chatService.getSessions();
        if (fetched && Array.isArray(fetched)) {
          setSessions(fetched.filter((s) => !s.isArchived));
        }
      } catch (err) {
        console.warn("[DashboardLayout] Load sessions error:", err);
      }
    };

    loadSessions();

    // Listen to session synchronization events
    const handleCreated = (e: Event) => {
      const customEvent = e as CustomEvent<BackendChatSession>;
      if (customEvent.detail) {
        setSessions((prev) => [customEvent.detail, ...prev.filter((s) => s.id !== customEvent.detail.id)]);
        setActiveSessionId(customEvent.detail.id);
      }
    };

    const handleUpdated = (e: Event) => {
      const customEvent = e as CustomEvent<BackendChatSession>;
      if (customEvent.detail) {
        setSessions((prev) =>
          prev.map((s) => (s.id === customEvent.detail.id ? { ...s, title: customEvent.detail.title } : s))
        );
      }
    };

    const handleArchived = (e: Event) => {
      const customEvent = e as CustomEvent<{ id: string }>;
      if (customEvent.detail) {
        setSessions((prev) => prev.filter((s) => s.id !== customEvent.detail.id));
      }
    };

    window.addEventListener("tameerai:session_created", handleCreated);
    window.addEventListener("tameerai:session_updated", handleUpdated);
    window.addEventListener("tameerai:session_archived", handleArchived);

    return () => {
      window.removeEventListener("tameerai:session_created", handleCreated);
      window.removeEventListener("tameerai:session_updated", handleUpdated);
      window.removeEventListener("tameerai:session_archived", handleArchived);
    };
  }, []);

  const handleLogout = async () => {
    try {
      await apiClient.post("/auth/logout").catch(() => {});
    } finally {
      apiClient.clearAuth();
      window.location.href = "/login";
    }
  };

  const handleCreateNewChat = () => {
    setActiveSessionId(null);
    setMobileSidebarOpen(false);

    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("tameerai:reset_chat"));
    }

    router.push(`/dashboard/ai-assistant?new=${Date.now()}`);
  };

  const handleSaveRename = async (sessionId: string) => {
    if (!editingTitle.trim()) {
      setEditingSessionId(null);
      return;
    }
    try {
      const updated = await chatService.updateSession(sessionId, { title: editingTitle.trim() });
      if (updated) {
        setSessions((prev) =>
          prev.map((s) => (s.id === sessionId ? { ...s, title: updated.title } : s))
        );
        if (typeof window !== "undefined") {
          window.dispatchEvent(new CustomEvent("tameerai:session_updated", { detail: updated }));
        }
      }
    } catch (err) {
      console.error("[DashboardLayout] Rename failed:", err);
    } finally {
      setEditingSessionId(null);
    }
  };

  const handleArchiveSession = async (sessionId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      const success = await chatService.archiveSession(sessionId);
      if (success) {
        setSessions((prev) => prev.filter((s) => s.id !== sessionId));
        if (typeof window !== "undefined") {
          window.dispatchEvent(new CustomEvent("tameerai:session_archived", { detail: { id: sessionId } }));
        }
        if (activeSessionId === sessionId) {
          setActiveSessionId(null);
          router.push(`/dashboard/ai-assistant?new=${Date.now()}`);
        }
      }
    } catch (err) {
      console.error("[DashboardLayout] Archive failed:", err);
    }
  };

  const displayName = currentUser?.full_name || "Engineer";
  const displayRole = currentUser?.role
    ? currentUser.role.replace(/_/g, " ").toUpperCase()
    : "CIVIL ENGINEER";
  const initials =
    displayName
      .split(" ")
      .filter(Boolean)
      .map((n) => n[0])
      .slice(0, 2)
      .join("")
      .toUpperCase() || "EN";

  const groupedSessions = groupSessions(sessions, searchSessionQuery);

  const SidebarContent = ({ isMobileDrawer = false }: { isMobileDrawer?: boolean }) => {
    const isExpanded = isMobileDrawer || sidebarOpen;
    return (
      <div className="flex flex-col h-full bg-white dark:bg-navy-900 border-r border-slate-200/80 dark:border-slate-800">
        {/* Brand Header */}
        <div className={cn(
          "flex items-center h-16 border-b border-slate-100 dark:border-slate-800/80 flex-shrink-0",
          isExpanded ? "justify-between px-3.5" : "justify-center px-2"
        )}>
          {isExpanded ? (
            <>
              <Link href="/dashboard" className="flex items-center" aria-label="TameerAI Dashboard">
                <img
                  src="/tameer_ai_orange.svg"
                  alt="TameerAI Construction Assistant"
                  className="h-10 sm:h-11 max-h-[44px] max-w-[170px] w-auto object-contain flex-shrink-0"
                />
              </Link>
              {!isMobileDrawer && (
                <button
                  type="button"
                  onClick={() => setSidebarOpen(false)}
                  className="hidden lg:flex p-1.5 rounded-lg text-slate-400 hover:text-orange-500 hover:bg-orange-50 dark:hover:bg-slate-800 transition-colors"
                  title={t("Collapse Sidebar", "سائیڈ بار بند کریں")}
                  aria-label="Collapse Sidebar"
                >
                  <PanelLeftClose className="w-4 h-4" />
                </button>
              )}
            </>
          ) : (
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="hidden lg:flex items-center justify-center p-1 rounded-xl text-slate-400 hover:text-orange-500 hover:bg-orange-50 dark:hover:bg-slate-800 transition-colors"
              title={t("Expand Sidebar", "سائیڈ بار کھولیں")}
              aria-label="Expand Sidebar"
            >
              <div className="w-10 h-10 overflow-hidden flex items-center justify-start flex-shrink-0 rounded-lg">
                <img
                  src="/tameer_ai_orange.svg"
                  alt="TameerAI"
                  width={120}
                  height={40}
                  className="h-10 w-[120px] max-w-none object-cover object-left flex-shrink-0"
                />
              </div>
            </button>
          )}
        </div>

        {/* Top CTA: + New Chat */}
        <div className="px-3 pt-3 pb-1 flex-shrink-0">
          {isExpanded ? (
            <button
              type="button"
              onClick={handleCreateNewChat}
              className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-orange-500 hover:bg-orange-600 active:scale-[0.98] text-white font-bold text-xs shadow-xs transition-all"
              title={t("Start new chat", "نئی چیٹ شروع کریں")}
            >
              <Plus className="w-4 h-4" />
              <span>{t("New Chat", "نئی چیٹ")}</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={handleCreateNewChat}
              className="w-full p-2 flex items-center justify-center rounded-xl bg-orange-500 hover:bg-orange-600 text-white shadow-xs transition-all"
              title={t("New Chat", "نئی چیٹ")}
            >
              <Plus className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Search Filter for Consultations */}
        {isExpanded && (
        <div className="px-3 py-1.5 flex-shrink-0">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchSessionQuery}
              onChange={(e) => setSearchSessionQuery(e.target.value)}
              placeholder={t("Filter conversations...", "گفتگو تلاش کریں...")}
              className="w-full pl-8 pr-7 py-1 text-xs rounded-lg bg-slate-100/80 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500/30"
            />
            {searchSessionQuery && (
              <button
                type="button"
                onClick={() => setSearchSessionQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Middle Section: Scrollable Consultations + Engineering Navigation */}
      <div className="flex-1 overflow-y-auto px-2.5 py-2 space-y-4">
        {/* Collapsed icon for AI Assistant */}
        {!isExpanded && (
          <div className="py-2 border-b border-slate-100 dark:border-slate-800/80 flex justify-center">
            <Link
              href="/dashboard/ai-assistant"
              className={cn(
                "p-2 rounded-xl transition-all",
                pathname === "/dashboard/ai-assistant"
                  ? "bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 shadow-2xs"
                  : "text-slate-400 hover:text-orange-500 hover:bg-slate-100 dark:hover:bg-navy-800"
              )}
              title={t("AI Assistant & Consultations", "اے آئی اسسٹنٹ اور مشاورتیں")}
            >
              <MessageSquare className="w-4 h-4" />
            </Link>
          </div>
        )}

        {/* Zone 1: Recent Consultations */}
        {isExpanded && (
          <div className="space-y-2">
            <div className="flex items-center justify-between px-1 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              <span className="flex items-center gap-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-orange-500" />
                {t("Recent Consultations", "حالیہ مشاورتیں")}
              </span>
              {sessions.length > 0 && (
                <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-100 dark:bg-navy-800 text-slate-500">
                  {sessions.length}
                </span>
              )}
            </div>

            {groupedSessions.length === 0 ? (
              <div className="p-3 text-center text-xs text-slate-400 dark:text-slate-500 bg-slate-50/50 dark:bg-navy-950/40 rounded-xl border border-dashed border-slate-200/80 dark:border-slate-800">
                {searchSessionQuery
                  ? t("No matching conversations.", "کوئی گفتگو نہیں ملی")
                  : t("No previous consultations.", "کوئی مشاورتی سیشن نہیں")}
              </div>
            ) : (
              <div className="space-y-2.5 max-h-48 overflow-y-auto pr-1">
                {groupedSessions.map((group) => (
                  <div key={group.id} className="space-y-1">
                    <div className="px-1 text-[9px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                      {t(group.labelEn, group.labelUr)}
                    </div>
                    {group.items.map((session) => {
                      const isSessionActive =
                        pathname === "/dashboard/ai-assistant" &&
                        (activeSessionId === session.id ||
                          (!activeSessionId && sessions[0]?.id === session.id));
                      const isEditing = editingSessionId === session.id;

                      return (
                        <div
                          key={session.id}
                          className={cn(
                            "group relative flex items-center justify-between rounded-xl px-2.5 py-1.5 text-xs transition-all",
                            isSessionActive
                              ? "bg-orange-500/10 text-orange-600 dark:text-orange-400 font-bold border border-orange-500/20 shadow-2xs"
                              : "text-slate-600 dark:text-slate-400 hover:bg-slate-100/70 dark:hover:bg-navy-800/60 hover:text-navy-900 dark:hover:text-white"
                          )}
                        >
                          {isEditing ? (
                            <div className="flex items-center gap-1 w-full" onClick={(e) => e.stopPropagation()}>
                              <input
                                type="text"
                                value={editingTitle}
                                onChange={(e) => setEditingTitle(e.target.value)}
                                onKeyDown={(e) => {
                                  if (e.key === "Enter") handleSaveRename(session.id);
                                  if (e.key === "Escape") setEditingSessionId(null);
                                }}
                                autoFocus
                                className="w-full text-xs px-1.5 py-0.5 rounded bg-white dark:bg-navy-800 border border-orange-500 text-slate-900 dark:text-white focus:outline-none"
                              />
                              <button
                                type="button"
                                onClick={() => handleSaveRename(session.id)}
                                className="p-1 text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/30 rounded"
                                title="Save title"
                              >
                                <Check className="w-3 h-3" />
                              </button>
                              <button
                                type="button"
                                onClick={() => setEditingSessionId(null)}
                                className="p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded"
                                title="Cancel"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                          ) : (
                            <>
                              <Link
                                href={`/dashboard/ai-assistant?session=${session.id}`}
                                onClick={() => {
                                  setActiveSessionId(session.id);
                                  setMobileSidebarOpen(false);
                                }}
                                className="flex-1 min-w-0 pr-1 truncate block text-left"
                                title={session.title}
                              >
                                <span className="truncate block">{session.title}</span>
                              </Link>

                              {/* Actions: Rename & Archive (Retention compliant soft-archive) */}
                              <div className="hidden group-hover:flex items-center gap-0.5 opacity-90">
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    setEditingSessionId(session.id);
                                    setEditingTitle(session.title);
                                  }}
                                  className="p-1 rounded text-slate-400 hover:text-orange-500 hover:bg-slate-200/60 dark:hover:bg-navy-700 transition-colors"
                                  title={t("Rename conversation", "نام تبدیل کریں")}
                                  aria-label="Rename conversation"
                                >
                                  <Pencil className="w-3 h-3" />
                                </button>
                                <button
                                  type="button"
                                  onClick={(e) => handleArchiveSession(session.id, e)}
                                  className="p-1 rounded text-slate-400 hover:text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-950/30 transition-colors"
                                  title={t("Archive conversation (Retention compliant)", "محفوظ کریں")}
                                  aria-label="Archive conversation"
                                >
                                  <Archive className="w-3 h-3" />
                                </button>
                              </div>
                            </>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Zone 2: Engineering Modules Navigation */}
        <div className="pt-2 border-t border-slate-100 dark:border-slate-800/80 space-y-1.5">
          {isExpanded && (
            <div className="flex items-center justify-between px-1 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              <span>{t("Engineering Modules", "انجینئرنگ ماڈیولز")}</span>
              <button
                type="button"
                onClick={() => setToolsCollapsed(!toolsCollapsed)}
                className="p-0.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                title={toolsCollapsed ? "Expand modules" : "Collapse modules"}
              >
                {toolsCollapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            </div>
          )}

          {(!toolsCollapsed || !isExpanded) && (
            <nav className="space-y-1">
              {engineeringNavItems.map((item) => {
                const Icon = item.icon;
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/dashboard" && pathname.startsWith(item.href));

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileSidebarOpen(false)}
                    className={cn(
                      "group flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition-all",
                      isActive
                        ? "bg-orange-500/10 text-orange-600 dark:text-orange-400 font-bold shadow-xs border border-orange-500/20"
                        : "text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white hover:bg-slate-100/70 dark:hover:bg-slate-800/60",
                      !isExpanded && "justify-center px-2"
                    )}
                    title={!isExpanded ? t(item.en, item.ur) : undefined}
                  >
                    <Icon
                      className={cn(
                        "w-4 h-4 flex-shrink-0 transition-transform group-hover:scale-110",
                        isActive
                          ? "text-orange-600 dark:text-orange-400"
                          : "text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-200"
                      )}
                    />
                    {isExpanded && (
                      <span className="flex-1 truncate">{t(item.en, item.ur)}</span>
                    )}
                    {isExpanded && item.badge && (
                      <span className="px-1.5 py-0.5 text-[9px] font-bold rounded-md bg-orange-100 dark:bg-orange-950 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-800">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </nav>
          )}
        </div>
      </div>

      {/* Bottom Section: Authenticated User Profile & System Controls */}
      <div className="p-3 border-t border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-navy-950/40 flex-shrink-0">
        {isExpanded ? (
          <div className="space-y-2.5">
            {/* User Profile Info */}
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 text-white font-black text-xs flex items-center justify-center flex-shrink-0 shadow-sm shadow-orange-500/20">
                {initials}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold text-navy-900 dark:text-white truncate">
                  {displayName}
                </p>
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 font-semibold truncate uppercase tracking-wider">
                    {displayRole}
                  </span>
                  {currentUser?.pec_number && (
                    <span
                      className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-slate-100 dark:bg-navy-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                      title={`PEC Registration: ${currentUser.pec_number}`}
                    >
                      PEC #{currentUser.pec_number}
                    </span>
                  )}
                </div>
                {currentUser?.company && (
                  <p className="text-[10px] text-slate-400 truncate mt-0.5">
                    {currentUser.company}
                  </p>
                )}
              </div>
              <button
                type="button"
                onClick={handleLogout}
                title={t("Logout", "لاگ آؤٹ")}
                className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                aria-label="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>

            {/* Settings & System Utilities Row */}
            <div className="pt-2 border-t border-slate-200/80 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <Link
                href="/dashboard/settings"
                onClick={() => setMobileSidebarOpen(false)}
                className={cn(
                  "flex items-center gap-1.5 hover:text-navy-900 dark:hover:text-white transition-colors py-1 px-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-navy-800",
                  pathname === "/dashboard/settings" && "text-orange-500 font-bold"
                )}
                title={t("Settings", "ترتیبات")}
              >
                <Settings className="w-3.5 h-3.5" />
                <span className="text-[11px] font-medium">{t("Settings", "ترتیبات")}</span>
              </Link>

              <div className="flex items-center gap-1">
                {/* Theme Toggle */}
                <button
                  type="button"
                  onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                  className="p-1 rounded-md hover:text-orange-500 hover:bg-slate-100 dark:hover:bg-navy-800 transition-colors"
                  title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
                  aria-label="Toggle theme"
                >
                  {theme === "dark" ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
                </button>

                {/* Language Toggle */}
                <button
                  type="button"
                  onClick={() => setLanguage(language === "en" ? "ur" : "en")}
                  className="p-1 rounded-md hover:text-orange-500 hover:bg-slate-100 dark:hover:bg-navy-800 transition-colors flex items-center gap-1 text-[10px] font-bold"
                  title="Toggle English / اردو"
                >
                  <Globe className="w-3.5 h-3.5 text-orange-500" />
                  <span>{language === "en" ? "اردو" : "EN"}</span>
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <div
              className="w-8 h-8 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 text-white font-black text-xs flex items-center justify-center shadow-xs cursor-pointer"
              title={`${displayName} (${displayRole})`}
              onClick={() => setSidebarOpen(true)}
            >
              {initials}
            </div>
            <button
              type="button"
              onClick={handleLogout}
              title={t("Logout", "لاگ آؤٹ")}
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 transition-colors"
              aria-label="Logout"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-navy-950 flex text-slate-900 dark:text-slate-100 font-sans">
      {/* Desktop Combined Sidebar */}
      <aside
        className={cn(
          "hidden lg:flex flex-col flex-shrink-0 transition-all duration-300 z-20",
          sidebarOpen ? "w-64 sm:w-72" : "w-16"
        )}
      >
        <SidebarContent />
      </aside>

      {/* Mobile Sidebar Overlay Drawer */}
      {mobileSidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="absolute inset-0 bg-navy-950/60 backdrop-blur-sm"
            onClick={() => setMobileSidebarOpen(false)}
          />
          <aside className="relative w-72 sm:w-80 bg-white dark:bg-navy-900 flex flex-col shadow-2xl z-10 animate-slide-in-right">
            <button
              onClick={() => setMobileSidebarOpen(false)}
              className="absolute top-4 right-4 p-2 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
              aria-label="Close menu"
            >
              <X className="w-5 h-5" />
            </button>
            <SidebarContent isMobileDrawer={true} />
          </aside>
        </div>
      )}

      {/* Main App Container */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Bar */}
        <header className="sticky top-0 z-30 bg-white/95 dark:bg-navy-900/95 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 px-4 lg:px-6 h-16 flex items-center justify-between gap-4 flex-shrink-0">
          {/* Left: Mobile Drawer Trigger + Global Search */}
          <div className="flex items-center gap-3 flex-1 max-w-xl">
            <button
              onClick={() => setMobileSidebarOpen(true)}
              className="lg:hidden p-2 rounded-xl text-slate-500 hover:text-navy-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
              aria-label="Toggle navigation"
              title={t("Open mobile menu", "موبائل مینو کھولیں")}
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Global Search Input Bar */}
            <div className="relative w-full">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Search className="w-4 h-4" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t(
                  "Search projects, building codes (PBC 2021), contracts...",
                  "منصوبے، بلڈنگ کوڈز (PBC 2021) یا معاہدات تلاش کریں..."
                )}
                className="w-full pl-9 pr-12 py-2 rounded-xl text-xs bg-slate-100/80 dark:bg-navy-950 border border-transparent focus:border-orange-500/40 dark:focus:border-orange-500/40 text-navy-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-500/20 transition-all"
              />
              <div className="hidden sm:flex absolute inset-y-0 right-0 pr-2.5 items-center">
                <kbd className="px-1.5 py-0.5 text-[10px] font-semibold text-slate-400 bg-white dark:bg-navy-800 border border-slate-200 dark:border-slate-700 rounded shadow-2xs">
                  ⌘K
                </kbd>
              </div>
            </div>
          </div>

          {/* Right: Quick Controls & User Profile Badge */}
          <div className="flex items-center gap-2.5 flex-shrink-0">
            {/* Language toggle: English | اردو */}
            <button
              type="button"
              onClick={() => setLanguage(language === "en" ? "ur" : "en")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100/80 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 hover:border-orange-500/40 transition-all shadow-2xs"
              title="Toggle English / اردو"
            >
              <Globe className="w-3.5 h-3.5 text-orange-500" />
              <span>{language === "en" ? "اردو" : "English"}</span>
            </button>

            {/* Theme toggle: Light | Dark */}
            <button
              type="button"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="p-2 rounded-xl text-slate-600 dark:text-slate-400 bg-slate-100/80 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 hover:text-orange-500 dark:hover:text-orange-400 transition-colors shadow-2xs"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            {/* Notification Bell */}
            <button
              className="relative p-2 rounded-xl text-slate-600 dark:text-slate-400 bg-slate-100/80 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 hover:text-orange-500 transition-colors shadow-2xs"
              aria-label="Notifications"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-orange-500 rounded-full ring-2 ring-white dark:ring-navy-900" />
            </button>

            {/* Profile Link Badge */}
            <Link
              href="/dashboard/settings"
              className="flex items-center gap-2.5 pl-2 border-l border-slate-200 dark:border-slate-800 hover:opacity-85 transition-opacity"
              title={displayName}
            >
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 text-white font-black text-xs flex items-center justify-center shadow-xs">
                {initials}
              </div>
              <div className="hidden md:block text-left">
                <p className="text-xs font-bold text-navy-900 dark:text-white leading-none truncate max-w-[120px]">
                  {displayName}
                </p>
                <p className="text-[10px] text-slate-400 mt-0.5 leading-none">
                  {displayRole}
                </p>
              </div>
            </Link>
          </div>
        </header>

        {/* Page Content Body */}
        <main className="flex-1 overflow-auto p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
