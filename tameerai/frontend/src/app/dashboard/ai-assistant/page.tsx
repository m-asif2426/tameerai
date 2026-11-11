/* eslint-disable @next/next/no-img-element */
"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  Send,
  User,
  BookOpen,
  Sparkles,
  MessageSquare,
  Copy,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Paperclip,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Plus,
  Search,
  Trash2,
  TrendingUp,
  ShieldAlert,
  PanelRightClose,
  PanelRightOpen,
  PanelLeftClose,
  PanelLeftOpen,
  Check,
  Building2,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { chatService, BackendChatSession, BackendChatMessage } from "@/services/chatService";
import { costService, CanonicalRateSnapshot } from "@/services/costService";
import { ChatWorkspace, DisplayMessage } from "@/components/chat";

function AIAssistantContent() {
  const { t, language } = useLanguage();
  const searchParams = useSearchParams();
  const router = useRouter();

  // Panel layout toggles (default false for clean Combined Sidebar view)
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(false);
  const [rightPanelOpen, setRightPanelOpen] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && window.innerWidth >= 1400) {
      setRightPanelOpen(true);
    }
  }, []);

  // Sessions state
  const [sessions, setSessions] = useState<BackendChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [searchHistoryQuery, setSearchHistoryQuery] = useState("");

  // Market Rates Panel
  const [selectedCity, setSelectedCity] = useState<string>("Lahore");
  const [rateSnapshots, setRateSnapshots] = useState<CanonicalRateSnapshot[]>([]);
  const [loadingRates, setLoadingRates] = useState(false);

  // Chat input and messages
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const chatBottomRef = useRef<HTMLDivElement>(null);
  const resetVersionRef = useRef(0);

  // Synchronize with URL search parameters (session and new-chat triggers)
  useEffect(() => {
    const isNew = searchParams?.get("new");
    const urlSid = searchParams?.get("session");

    if (isNew) {
      // Universal New Chat triggered across routes: display clean Welcome Screen
      resetVersionRef.current += 1;
      setActiveSessionId("");
      setMessages([]);
      setInputMessage("");
      if (typeof window !== "undefined") {
        window.history.replaceState({}, "", "/dashboard/ai-assistant");
      }
      return;
    }

    if (urlSid) {
      if (urlSid !== activeSessionId) {
        setActiveSessionId(urlSid);
      }
    }
  }, [searchParams, activeSessionId]);

  // Load chat sessions on mount and subscribe to synchronization events
  useEffect(() => {
    async function loadSessions() {
      try {
        const fetchedSessions = await chatService.getSessions();
        if (fetchedSessions && Array.isArray(fetchedSessions)) {
          const activeList = fetchedSessions.filter((s) => !s.isArchived);
          setSessions(activeList);
          const currentUrlSid = typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("session") : null;
          if (currentUrlSid && activeList.some((s) => s.id === currentUrlSid)) {
            setActiveSessionId(currentUrlSid);
          }
          // Intentionally do NOT force-restore activeList[0] when session param is absent.
        }
      } catch (err) {
        console.error("[AIAssistant] Error loading sessions:", err);
      }
    }
    loadSessions();

    const handleCreated = (e: Event) => {
      const customEvent = e as CustomEvent<BackendChatSession>;
      if (customEvent.detail) {
        setSessions((prev) => [customEvent.detail, ...prev.filter((s) => s.id !== customEvent.detail.id)]);
      }
    };

    const handleArchived = (e: Event) => {
      const customEvent = e as CustomEvent<{ id: string }>;
      if (customEvent.detail) {
        setSessions((prev) => prev.filter((s) => s.id !== customEvent.detail.id));
        if (activeSessionId === customEvent.detail.id) {
          setActiveSessionId("");
          setMessages([]);
        }
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

    const handleReset = () => {
      resetVersionRef.current += 1;
      setActiveSessionId("");
      setMessages([]);
      setInputMessage("");
      if (typeof window !== "undefined") {
        window.history.replaceState({}, "", "/dashboard/ai-assistant");
      }
    };

    window.addEventListener("tameerai:reset_chat", handleReset);
    window.addEventListener("tameerai:session_created", handleCreated);
    window.addEventListener("tameerai:session_archived", handleArchived);
    window.addEventListener("tameerai:session_updated", handleUpdated);

    return () => {
      window.removeEventListener("tameerai:reset_chat", handleReset);
      window.removeEventListener("tameerai:session_created", handleCreated);
      window.removeEventListener("tameerai:session_archived", handleArchived);
      window.removeEventListener("tameerai:session_updated", handleUpdated);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // When activeSessionId changes, fetch messages
  useEffect(() => {
    if (!activeSessionId) return;
    let cancelled = false;
    const currentVersion = resetVersionRef.current;

    async function loadMessages() {
      try {
        const fetched = await chatService.getMessages(activeSessionId);
        if (cancelled || resetVersionRef.current !== currentVersion) return;

        if (fetched && fetched.length > 0) {
          const mapped: DisplayMessage[] = [];
          for (const m of fetched) {
            mapped.push({
              id: m.id || m.uuid || `msg-${m.sequenceNumber}`,
              role: (m.role as "user" | "assistant") || "user",
              content: m.content,
              contentUrdu: m.contentUrdu,
              timestamp: m.createdAt
                ? new Date(m.createdAt).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
                : "Just now",
              citations: m.citations,
            });
            if (m.role === "user") {
              const advisory = chatService.getDeterministicAdvisory(m.content, language);
              mapped.push({
                id: `advisory-${m.id || m.sequenceNumber}`,
                role: "assistant",
                content: advisory.content,
                contentUrdu: advisory.contentUrdu,
                timestamp: m.createdAt
                  ? new Date(m.createdAt).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
                  : "Just now",
                citations: advisory.citations,
              });
            }
          }
          if (!cancelled && resetVersionRef.current === currentVersion) {
            setMessages(mapped);
          }
        } else {
          if (!cancelled && resetVersionRef.current === currentVersion) {
            setMessages((prev) => (prev.length > 0 ? prev : []));
          }
        }
      } catch (err) {
        console.warn("[AIAssistant] Error loading messages:", err);
      }
    }
    loadMessages();

    return () => {
      cancelled = true;
    };
  }, [activeSessionId, language]);

  // Load live rate snapshots for right-hand panel
  useEffect(() => {
    async function loadRates() {
      setLoadingRates(true);
      try {
        const snapshots = await costService.getSnapshots(selectedCity);
        setRateSnapshots(snapshots);
      } catch (err) {
        console.error("[AIAssistant] Error loading rates:", err);
        setRateSnapshots([]);
      } finally {
        setLoadingRates(false);
      }
    }
    loadRates();
  }, [selectedCity]);

  const scrollToBottom = () => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleCreateSession = async () => {
    const defaultTitle = `Engineering Consultation ${sessions.length + 1}`;
    const newSession = await chatService.createSession({
      title: defaultTitle,
      sessionType: "general",
      language: language === "ur" ? "ur" : "en",
    });
    if (newSession) {
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("tameerai:session_created", { detail: newSession }));
        window.history.replaceState({}, "", `/dashboard/ai-assistant?session=${newSession.id}`);
      }
      setMessages([]);
    }
  };

  const handleSendMessage = async (customText?: string) => {
    const textToSend = customText || inputMessage;
    if (!textToSend.trim()) return;

    const opVersion = resetVersionRef.current;
    setInputMessage("");

    const userMsg: DisplayMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: textToSend,
      contentUrdu: textToSend,
      timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
    };

    // Generate deterministic response directly from official building codes
    const advisory = chatService.getDeterministicAdvisory(textToSend, language);

    const assistantMsg: DisplayMessage = {
      id: `assistant-${Date.now()}`,
      role: "assistant",
      content: advisory.content,
      contentUrdu: advisory.contentUrdu,
      timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      citations: advisory.citations,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);

    // Persist session and user message to genuine local backend
    try {
      let currentSessionId = activeSessionId;
      if (!currentSessionId) {
        const sessionTitle = textToSend.length > 35 ? textToSend.slice(0, 32) + "..." : textToSend;
        const newSession = await chatService.createSession({
          title: sessionTitle,
          sessionType: "general",
          language: language === "ur" ? "ur" : "en",
        });

        // Abort if user clicked New Chat while creation was in-flight
        if (resetVersionRef.current !== opVersion) return;

        if (newSession) {
          currentSessionId = newSession.id;
          setActiveSessionId(newSession.id);
          setSessions((prev) => [newSession, ...prev.filter((s) => s.id !== newSession.id)]);
          if (typeof window !== "undefined") {
            window.dispatchEvent(new CustomEvent("tameerai:session_created", { detail: newSession }));
            window.history.replaceState({}, "", `/dashboard/ai-assistant?session=${newSession.id}`);
          }

          if (resetVersionRef.current !== opVersion) return;

          await chatService.createMessage(currentSessionId, {
            content: textToSend,
            role: "user",
            language: language === "ur" ? "ur" : "en",
          });
        }
      } else if (currentSessionId) {
        if (resetVersionRef.current !== opVersion) return;
        await chatService.createMessage(currentSessionId, {
          content: textToSend,
          role: "user",
          language: language === "ur" ? "ur" : "en",
        });
      }
    } catch (err) {
      console.warn("[AIAssistant] Background message persist failed:", err);
    }
  };

  const handleCopyMessage = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="flex h-[calc(100vh-5rem)] overflow-hidden rounded-2xl bg-white dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 shadow-2xs font-sans">
      {/* ========================================================================= */}
      {/* LEFT SIDEBAR: SESSIONS HISTORY                                            */}
      {/* ========================================================================= */}
      <div
        className={cn(
          "flex-col border-r border-slate-200/80 dark:border-slate-800 bg-slate-50/70 dark:bg-navy-900/50 transition-all duration-200 z-10",
          leftSidebarOpen ? "w-64 sm:w-72 flex" : "hidden"
        )}
      >
        {/* Header */}
        <div className="p-3.5 border-b border-slate-200/80 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-orange-500" />
            <span className="text-xs font-bold text-navy-900 dark:text-white">
              {t("Advisory Sessions", "مشاورتی سیشنز")}
            </span>
          </div>
          <button
            onClick={handleCreateSession}
            className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-bold bg-orange-500 text-white hover:bg-orange-600 shadow-2xs"
            title="Start New Session"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>{t("New", "نیا")}</span>
          </button>
        </div>

        {/* Search */}
        <div className="p-2 border-b border-slate-200/80 dark:border-slate-800">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder={t("Filter sessions...", "سیشن تلاش کریں...")}
              value={searchHistoryQuery}
              onChange={(e) => setSearchHistoryQuery(e.target.value)}
              className="w-full text-xs pl-8 pr-2 py-1 rounded-lg bg-white dark:bg-navy-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none"
            />
          </div>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-400">
              {t("No chat sessions in DB yet.", "کوئی محفوظ سیشن نہیں ہے۔")}
            </div>
          ) : (
            sessions
              .filter((s) => !searchHistoryQuery || s.title.toLowerCase().includes(searchHistoryQuery.toLowerCase()))
              .map((session) => (
                <button
                  key={session.id}
                  onClick={() => setActiveSessionId(session.id)}
                  className={cn(
                    "w-full text-left p-2.5 rounded-xl text-xs transition-all flex flex-col gap-0.5",
                    activeSessionId === session.id
                      ? "bg-white dark:bg-navy-800 text-navy-900 dark:text-white font-bold shadow-2xs border border-slate-200/80 dark:border-slate-700"
                      : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-navy-800/50"
                  )}
                >
                  <span className="truncate">{session.title}</span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {session.sessionType} · {session.messageCount || 0} msgs
                  </span>
                </button>
              ))
          )}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* MAIN CHAT WORKSPACE (Phase 02B Modular Architecture)                       */}
      {/* ========================================================================= */}
      <ChatWorkspace
        messages={messages}
        activeSessionId={activeSessionId}
        activeSessionTitle={sessions.find((s) => s.id === activeSessionId)?.title}
        inputMessage={inputMessage}
        onInputChange={setInputMessage}
        onSendMessage={handleSendMessage}
        leftSidebarOpen={leftSidebarOpen}
        rightPanelOpen={rightPanelOpen}
        onToggleLeftSidebar={() => setLeftSidebarOpen(!leftSidebarOpen)}
        onToggleRightPanel={() => setRightPanelOpen(!rightPanelOpen)}
        copiedId={copiedId}
        onCopyMessage={handleCopyMessage}
        chatBottomRef={chatBottomRef}
        language={language}
      />

      {/* ========================================================================= */}
      {/* RIGHT SIDEBAR: LIVE MATERIAL RATES & OFFICIAL CODES REFERENCE             */}
      {/* ========================================================================= */}
      <div
        className={cn(
          "flex-col border-l border-slate-200/80 dark:border-slate-800 bg-slate-50/70 dark:bg-navy-900/50 transition-all duration-200 z-10",
          rightPanelOpen ? "w-72 sm:w-80 flex" : "hidden"
        )}
      >
        {/* City Selector */}
        <div className="p-3.5 border-b border-slate-200/80 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4 text-orange-500" />
            <span className="text-xs font-bold text-navy-900 dark:text-white">
              {t("Stored PostgreSQL Rates", "محفوظ شدہ مارکیٹ ریٹس")}
            </span>
          </div>
          <select
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            className="text-[11px] font-bold px-2 py-1 rounded-lg bg-white dark:bg-navy-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200"
          >
            <option value="Lahore">Lahore</option>
            <option value="Karachi">Karachi</option>
            <option value="Islamabad">Islamabad</option>
          </select>
        </div>

        {/* Stored Snapshots */}
        <div className="p-3 border-b border-slate-200/80 dark:border-slate-800 flex-1 overflow-y-auto space-y-2">
          {loadingRates ? (
            <div className="p-4 text-center text-xs text-slate-400">
              {t("Loading rate snapshots...", "ریٹس لوڈ ہو رہے ہیں...")}
            </div>
          ) : rateSnapshots.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-400">
              {t("No rate snapshots available.", "کوئی ریٹ موجود نہیں")}
            </div>
          ) : (
            rateSnapshots.map((item, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded-xl bg-white dark:bg-navy-800 border border-slate-200/80 dark:border-slate-700 shadow-2xs space-y-1"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-navy-900 dark:text-white truncate">
                    {item.product_name}
                  </span>
                  <span className="font-mono font-bold text-orange-600 dark:text-orange-400">
                    PKR {item.rate_pkr.toLocaleString("en-PK")}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[10px] text-slate-400">
                  <span>
                    {item.unit}
                    {item.snapshot_at && (
                      <span className="ml-1 opacity-70">
                        · {new Date(item.snapshot_at).toLocaleDateString()}
                      </span>
                    )}
                  </span>
                  <span className="capitalize px-1.5 py-0.2 rounded bg-slate-100 dark:bg-navy-900 text-slate-600 dark:text-slate-300">
                    {item.verification_status}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Statutory Code Guidance Box */}
        <div className="p-3.5 space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-bold text-navy-900 dark:text-white">
            <BookOpen className="w-4 h-4 text-emerald-500" />
            <span>{t("Statutory Reference Guidance", "ریفرنس کوڈز رہنمائی")}</span>
          </div>
          <div className="p-2.5 rounded-xl bg-white dark:bg-navy-800 border border-slate-200 dark:border-slate-700 text-[11px] text-slate-600 dark:text-slate-300 space-y-1 leading-snug">
            <p className="font-bold text-slate-800 dark:text-slate-100">Pakistan Building Code (PBC 2021)</p>
            <p>Seismic Provisions: BCP SP-2021</p>
            <p>Provincial Bylaws: LDA 2019 / CDA 2020 / SBCA</p>
            <p>Contracts: FIDIC Red/Yellow Books & PEC SBD</p>
            <p className="text-[10px] text-slate-400 pt-1 border-t border-slate-200/60 dark:border-slate-700/60">
              {t("Notice: Guidance requires independent verification against official gazette publications.", "نوٹ: مستند سرکاری گزٹ سے تصدیق لازمی ہے۔")}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AIAssistantPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-[calc(100vh-5rem)] items-center justify-center bg-white dark:bg-navy-950 rounded-2xl border border-slate-200/80 dark:border-slate-800">
          <div className="flex items-center gap-2 text-slate-500 text-sm">
            <RefreshCw className="w-4 h-4 animate-spin text-orange-500" />
            <span>Loading TameerAI Assistant...</span>
          </div>
        </div>
      }
    >
      <AIAssistantContent />
    </Suspense>
  );
}
