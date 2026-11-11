"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  Building2,
  MapPin,
  Calendar,
  Users,
  TrendingUp,
  ShieldCheck,
  Search,
  Filter,
  Plus,
  Eye,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  UploadCloud,
  ChevronRight,
  Layers,
  ArrowRight,
  Sparkles,
  MessageSquare,
  FileCheck2,
  Download,
  AlertCircle,
  Coins,
  FolderOpen,
  FileSpreadsheet,
  FileCode,
  HardHat,
  Send,
  Bot,
  User,
  Check,
  X,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Project, ProjectDocument } from "@/types";
import { projectService, ProjectActivity } from "@/services/projectService";

type WorkspaceTab =
  | "overview"
  | "ai-chat"
  | "documents"
  | "compliance"
  | "contract"
  | "cost"
  | "reports";

export default function ProjectWorkspacePage() {
  const { t } = useLanguage();
  const params = useParams();
  const projectId = (params?.id as string) || "";

  const [project, setProject] = useState<Project | null>(null);
  const [documents, setDocuments] = useState<ProjectDocument[]>([]);
  const [activities, setActivities] = useState<ProjectActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("overview");

  // Chat message state for AI Chat tab (deterministic rule-based assistant mode)
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<
    { sender: "bot" | "user"; text: string; time: string }[]
  >([]);

  // Load project details dynamically
  const loadProjectData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setNotFound(false);
    try {
      const p = await projectService.getProjectById(projectId);
      if (!p) {
        setNotFound(true);
        setProject(null);
        return;
      }
      setProject(p);

      // Initialize workspace chat greeting
      setChatMessages([
        {
          sender: "bot",
          text: `Workspace initialized for ${p.name} (${p.id}). Deterministic building code advisory active (PBC 2021). Neural LLM features are disabled per safety policy.`,
          time: "Ready",
        },
      ]);

      const [docs, acts] = await Promise.all([
        projectService.getProjectDocuments(p.id),
        projectService.getProjectActivities(p.id),
      ]);
      setDocuments(docs);
      setActivities(acts);
    } catch (err) {
      console.error("[ProjectDetail] Error loading project:", err);
      setNotFound(true);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadProjectData();
  }, [loadProjectData]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || !project) return;

    const userText = chatInput.trim();
    const userMsg = { sender: "user" as const, text: userText, time: "Just now" };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput("");

    // Deterministic rule-based response
    setTimeout(() => {
      const botMsg = {
        sender: "bot" as const,
        text: `Rule Advisory for [${project.name}]: Structural queries regarding ${project.city} are evaluated against PBC 2021 guidelines. For life-safety hazards, consult /dashboard/safety.`,
        time: "Just now",
      };
      setChatMessages((prev) => [...prev, botMsg]);
    }, 400);
  };

  // Loading Skeleton State
  if (loading) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto p-4 animate-pulse">
        <div className="h-5 bg-slate-200 dark:bg-slate-800 rounded w-48 mb-4" />
        <div className="h-44 bg-white dark:bg-navy-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-8" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-slate-800" />
          ))}
        </div>
      </div>
    );
  }

  // Genuine 404 / Not Found State
  if (notFound || !project) {
    return (
      <div className="max-w-2xl mx-auto py-16 px-4 text-center">
        <div className="w-16 h-16 rounded-2xl bg-amber-500/10 text-amber-500 border border-amber-500/20 flex items-center justify-center mx-auto mb-4">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h1 className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white mb-2">
          {t("Project Not Found", "منصوبہ نہیں ملا (404)")}
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mb-6 leading-relaxed">
          {t(
            `No construction project workspace exists with identifier "${projectId}" in your authorized organization. It may have been removed or access permissions were revoked.`,
            `آئی ڈی "${projectId}" کے تحت کوئی تعمیراتی منصوبہ ریکارڈ نہیں ہے۔ براہ کرم اپنے پروجیکٹس کی فہرست چیک کریں۔`
          )}
        </p>
        <Link
          href="/dashboard/projects"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs uppercase tracking-wider shadow-md shadow-orange-500/20 transition-all"
        >
          <FolderOpen className="w-4 h-4" />
          <span>{t("Back to Project Portfolio", "منصوبوں کی فہرست پر واپس جائیں")}</span>
        </Link>
      </div>
    );
  }

  const tabs: {
    key: WorkspaceTab;
    labelEn: string;
    labelUr: string;
    icon: React.ComponentType<{ className?: string }>;
    count?: number;
  }[] = [
    { key: "overview", labelEn: "Overview", labelUr: "خلاصہ (Overview)", icon: Layers },
    { key: "ai-chat", labelEn: "Advisory Chat", labelUr: "مشاورتی چیٹ", icon: MessageSquare },
    { key: "documents", labelEn: "Documents", labelUr: "دستاویزات", icon: FolderOpen, count: documents.length },
    { key: "compliance", labelEn: "Compliance", labelUr: "تعمیل (Compliance)", icon: ShieldCheck },
    { key: "contract", labelEn: "Contract", labelUr: "معاہدہ (Contract)", icon: FileText },
    { key: "cost", labelEn: "Cost Intelligence", labelUr: "لاگت انٹیلی جنس", icon: Coins },
    { key: "reports", labelEn: "Reports", labelUr: "رپورٹس (Reports)", icon: FileCheck2 },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans">
      {/* 1. TOP BREADCRUMB */}
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <Link
          href="/dashboard/projects"
          className="hover:text-orange-500 transition-colors font-medium"
        >
          {t("My Projects", "میرے منصوبے")}
        </Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-navy-900 dark:text-white font-bold">
          {t(project.name, project.nameUrdu)}
        </span>
        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
          {project.id}
        </span>
      </div>

      {/* 2. TOP HERO SECTION */}
      <div className="rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-slate-100 dark:border-slate-800/80">
          {/* Left Details */}
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white tracking-tight">
                {t(project.name, project.nameUrdu)}
              </h1>

              {/* Status Badge */}
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800 inline-flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                <span>{t(project.status, project.statusUrdu)}</span>
              </span>

              {/* Risk Badge */}
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 inline-flex items-center gap-1.5">
                <span>{t(project.risk, project.riskUrdu)} {t("Risk", "خطرہ")}</span>
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
              <span className="flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-orange-500 flex-shrink-0" />
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  {t(project.location, project.locationUrdu)} ({project.city})
                </span>
              </span>
              <span className="flex items-center gap-1.5">
                <Building2 className="w-4 h-4 text-slate-400 flex-shrink-0" />
                <span>{t(project.type, project.typeUrdu)}</span>
              </span>
              <span className="flex items-center gap-1.5">
                <HardHat className="w-4 h-4 text-slate-400 flex-shrink-0" />
                <span>{project.engineer || "Project Engineer"}</span>
              </span>
            </div>
          </div>

          {/* Right Action Buttons */}
          <div className="flex items-center gap-2.5 self-start lg:self-auto flex-wrap">
            <button
              onClick={() => setActiveTab("ai-chat")}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs uppercase tracking-wider shadow-md shadow-orange-500/20 transition-all active:scale-95"
            >
              <Sparkles className="w-4 h-4" />
              <span>{t("Advisory Chat", "مشاورتی چیٹ")}</span>
            </button>
            <button
              onClick={() => setActiveTab("documents")}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-bold text-xs uppercase tracking-wider border border-slate-200 dark:border-slate-700 transition-colors"
            >
              <UploadCloud className="w-4 h-4 text-orange-500" />
              <span>{t("Upload DWG / PDF", "ڈرائنگ اپ لوڈ کریں")}</span>
            </button>
          </div>
        </div>

        {/* Metric Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              {t("Approved Budget", "منظور شدہ بجٹ")}
            </span>
            <div className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white mt-0.5 font-mono">
              PKR {project.budgetCrore.toFixed(1)} {t("Crore", "کروڑ")}
            </div>
            <span className="text-[11px] text-slate-400">
              {t("Spent: PKR", "خرچ ہوا: PKR")} {project.spentCrore.toFixed(1)} {t("Cr", "کروڑ")}
            </span>
          </div>

          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              {t("PBC 2021 Compliance", "پی بی سی 2021 تعمیل")}
            </span>
            <div className="text-xl sm:text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-0.5 flex items-center gap-1.5">
              <span>{project.complianceScore ?? 100}%</span>
              <ShieldCheck className="w-5 h-5 text-emerald-500" />
            </div>
            <span className="text-[11px] text-slate-400">
              {t("Bylaw Clearance Benchmark", "ضوابط کی جانچ")}
            </span>
          </div>

          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              {t("Covered Area & Floors", "رقبہ اور منزلیں")}
            </span>
            <div className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white mt-0.5">
              {project.floors} {t("Floors", "منزلیں")}
            </div>
            <span className="text-[11px] text-slate-400 font-mono">
              {project.areaSqft || "N/A"}
            </span>
          </div>

          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              {t("Jurisdiction Authority", "متعلقہ اتھارٹی")}
            </span>
            <div className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white mt-0.5">
              {project.governingAuthority || `${project.city} Development Authority`}
            </div>
            <span className="text-[11px] text-slate-400">
              {t("Statutory Jurisdiction", "قانونی دائرہ اختیار")}
            </span>
          </div>
        </div>
      </div>

      {/* 3. WORKSPACE TABS */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 overflow-x-auto pb-px">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                "flex items-center gap-2 px-4 py-3 text-xs font-bold border-b-2 transition-all whitespace-nowrap",
                isActive
                  ? "border-orange-500 text-orange-600 dark:text-orange-400 bg-orange-50/50 dark:bg-orange-950/20 rounded-t-xl"
                  : "border-transparent text-slate-500 hover:text-navy-900 dark:hover:text-white hover:border-slate-300"
              )}
            >
              <Icon className="w-4 h-4" />
              <span>{t(tab.labelEn, tab.labelUr)}</span>
              {typeof tab.count === "number" && (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* 4. TAB CONTENTS */}
      {/* Overview Tab */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Project Summary */}
            <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
              <h2 className="text-sm font-bold text-navy-900 dark:text-white uppercase tracking-wider mb-3">
                {t("Workspace Summary", "ورک اسپیس کا خلاصہ")}
              </h2>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed mb-4">
                {project.description ||
                  t(
                    `Active construction workspace for ${project.name}, located in ${project.location}, under ${project.city} municipal building codes. All safety assessments, compliance checks, and material rate intelligence are isolated to this project.`,
                    `منصوبہ ${project.name} کا فعال ورک اسپیس، جو کہ ${project.location} میں واقع ہے۔`
                  )}
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-100 dark:border-slate-800 text-xs">
                <div>
                  <span className="text-slate-400 block">{t("Project Code", "کوڈ")}</span>
                  <span className="font-mono font-bold text-navy-900 dark:text-white">{project.id}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">{t("City", "شہر")}</span>
                  <span className="font-bold text-navy-900 dark:text-white">{project.city}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">{t("Status", "حیثیت")}</span>
                  <span className="font-bold text-amber-600 dark:text-amber-400">{project.status}</span>
                </div>
              </div>
            </div>

            {/* Attached Documents Preview */}
            <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-bold text-navy-900 dark:text-white uppercase tracking-wider">
                  {t("Project Documents", "منصوبے کی دستاویزات")} ({documents.length})
                </h2>
                <button
                  onClick={() => setActiveTab("documents")}
                  className="text-xs text-orange-500 font-bold hover:underline"
                >
                  {t("View All", "سب دیکھیں")}
                </button>
              </div>

              {documents.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl p-4">
                  <FolderOpen className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                  <p>{t("No documents attached yet.", "ابھی تک کوئی دستاویز منسلک نہیں ہے۔")}</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {documents.slice(0, 3).map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/60 dark:border-slate-800 text-xs"
                    >
                      <div className="flex items-center gap-2.5">
                        <FileText className="w-4 h-4 text-orange-500" />
                        <div>
                          <p className="font-bold text-navy-900 dark:text-white">{doc.name}</p>
                          <p className="text-[10px] text-slate-400">{doc.size} • {doc.uploadedBy}</p>
                        </div>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-600">
                        {doc.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right: Activity Log */}
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
              <h2 className="text-sm font-bold text-navy-900 dark:text-white uppercase tracking-wider mb-4">
                {t("Audit Activity Trail", "آڈٹ سرگرمیوں کا لاگ")}
              </h2>
              {activities.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl p-4">
                  <Clock className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                  <p>{t("No activity logged yet.", "ابھی تک کوئی سرگرمی ریکارڈ نہیں ہوئی۔")}</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {activities.map((act) => (
                    <div
                      key={act.id}
                      className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/60 dark:border-slate-800 text-xs"
                    >
                      <p className="font-bold text-navy-900 dark:text-white">{act.action}</p>
                      <span className="text-[10px] text-slate-400">
                        {new Date(act.created_at).toLocaleString()} • {act.actor_name || "Engineer"}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Advisory Chat Tab */}
      {activeTab === "ai-chat" && (
        <div className="bg-white dark:bg-navy-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm">
          <div className="mb-4 pb-3 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-orange-500" />
              <h2 className="text-sm font-bold text-navy-900 dark:text-white">
                {t("Deterministic Building Code Advisory Mode", "قواعد وضوابط مشاورتی موڈ")}
              </h2>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-900">
              AI Neural Inference Offline (Safety Policy)
            </span>
          </div>

          <div className="h-80 overflow-y-auto space-y-3 p-2 mb-4 bg-slate-50 dark:bg-navy-950 rounded-2xl border border-slate-200/60 dark:border-slate-800 text-xs">
            {chatMessages.map((msg, i) => (
              <div
                key={i}
                className={cn(
                  "flex gap-2 max-w-xl",
                  msg.sender === "user" ? "ml-auto justify-end" : "justify-start"
                )}
              >
                {msg.sender === "bot" && (
                  <div className="w-6 h-6 rounded-lg bg-orange-500 text-white flex items-center justify-center flex-shrink-0">
                    <Bot className="w-3.5 h-3.5" />
                  </div>
                )}
                <div
                  className={cn(
                    "p-3 rounded-2xl",
                    msg.sender === "user"
                      ? "bg-orange-500 text-white"
                      : "bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 text-navy-900 dark:text-white"
                  )}
                >
                  <p>{msg.text}</p>
                  <span className="text-[9px] opacity-70 block mt-1">{msg.time}</span>
                </div>
              </div>
            ))}
          </div>

          <form onSubmit={handleSendMessage} className="flex gap-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder={t(
                `Ask about PBC 2021 or LDA bylaws for ${project.name}...`,
                `اس منصوبے کے متعلق سوال درج کریں...`
              )}
              className="flex-1 px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-xs text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20"
            />
            <button
              type="submit"
              className="px-4 py-2.5 bg-orange-500 hover:bg-orange-600 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}

      {/* Documents Tab */}
      {activeTab === "documents" && (
        <div className="bg-white dark:bg-navy-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-base font-bold text-navy-900 dark:text-white">
                {t("Workspace Documents", "ورک اسپیس کی دستاویزات")}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {t("Blueprints, CAD drawings, BOQ spreadsheets, and structural submittals.", "نقشہ جات اور شیٹس")}
              </p>
            </div>
            <button className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-orange-500 hover:bg-orange-600 text-white text-xs font-bold transition-all">
              <UploadCloud className="w-4 h-4" />
              <span>{t("Upload New Document", "نئی دستاویز اپ لوڈ کریں")}</span>
            </button>
          </div>

          {documents.length === 0 ? (
            <div className="text-center py-16 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl">
              <FolderOpen className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-navy-900 dark:text-white mb-1">
                {t("No Documents Uploaded Yet", "کوئی دستاویز اپ لوڈ نہیں کی گئی")}
              </h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mb-4">
                {t("Upload PDF blueprints, CAD (.dwg) files, or Excel (.xlsx) BOQ schedules to start automatic verification.", "فائل اپ لوڈ کر کے آڈٹ شروع کریں۔")}
              </p>
            </div>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="p-4 rounded-2xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800"
                >
                  <div className="flex items-start justify-between mb-3">
                    <FileText className="w-6 h-6 text-orange-500" />
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950 text-emerald-600">
                      {doc.status}
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-navy-900 dark:text-white truncate mb-1">
                    {doc.name}
                  </h4>
                  <p className="text-[11px] text-slate-400">
                    {doc.size} • {doc.uploadedBy}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Compliance Tab */}
      {activeTab === "compliance" && (
        <div className="p-8 rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 text-center shadow-sm">
          <ShieldCheck className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
          <h2 className="text-base font-bold text-navy-900 dark:text-white mb-2">
            {t("Building Code Compliance Evaluation", "بلڈنگ کوڈ تعمیل کا جائزہ")}
          </h2>
          <p className="text-xs text-slate-500 max-w-md mx-auto mb-6">
            {t(
              "To audit setbacks, FAR, height zoning, and egress corridors against PBC 2021 bylaws, initiate a new audit for this workspace.",
              "پی بی سی 2021 کے تحت سیٹ بیک اور بلڈنگ ہائٹ کی جانچ کے لیے نیا آڈٹ شروع کریں۔"
            )}
          </p>
          <Link
            href="/dashboard/audit"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs uppercase tracking-wider transition-all"
          >
            <span>{t("Launch Code Audit", "کوڈ آڈٹ شروع کریں")}</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Contract Tab */}
      {activeTab === "contract" && (
        <div className="p-8 rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 text-center shadow-sm">
          <FileText className="w-12 h-12 text-blue-500 mx-auto mb-3" />
          <h2 className="text-base font-bold text-navy-900 dark:text-white mb-2">
            {t("Contract Risk Analysis", "معاہداتی خطرات کا تجزیہ")}
          </h2>
          <p className="text-xs text-slate-500 max-w-md mx-auto mb-6">
            {t(
              "No contract documents analyzed for this workspace yet. Upload your FIDIC or contractor agreement in the Contract Analyzer.",
              "اس ورک اسپیس کے لیے ابھی تک کوئی معاہدہ اپ لوڈ نہیں کیا گیا۔"
            )}
          </p>
          <Link
            href="/dashboard/contracts"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs uppercase tracking-wider transition-all"
          >
            <span>{t("Open Contract Analyzer", "کنٹریکٹ اینالائزر کھولیں")}</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Cost Intelligence Tab */}
      {activeTab === "cost" && (
        <div className="p-8 rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 text-center shadow-sm">
          <Coins className="w-12 h-12 text-orange-500 mx-auto mb-3" />
          <h2 className="text-base font-bold text-navy-900 dark:text-white mb-2">
            {t("Cost & Material Rate Intelligence", "لاگت اور میٹریل ریٹس")}
          </h2>
          <p className="text-xs text-slate-500 max-w-md mx-auto mb-6">
            {t(
              `View canonical wholesale market rates and PBS retail benchmarks for ${project.city}. Track price volatility and BOQ estimates.`,
              `شہر ${project.city} کے لیے تصدیق شدہ مارکیٹ ریٹس کا جائزہ لیں۔`
            )}
          </p>
          <Link
            href="/dashboard/costs"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs uppercase tracking-wider transition-all"
          >
            <span>{t("View Live Market Rates", "مارکیٹ ریٹس دیکھیں")}</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Reports Tab */}
      {activeTab === "reports" && (
        <div className="p-8 rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 text-center shadow-sm">
          <FileCheck2 className="w-12 h-12 text-purple-500 mx-auto mb-3" />
          <h2 className="text-base font-bold text-navy-900 dark:text-white mb-2">
            {t("Formal Engineering Dossiers", "باضابطہ انجینئرنگ رپورٹس")}
          </h2>
          <p className="text-xs text-slate-500 max-w-md mx-auto mb-6">
            {t(
              "No formal reports compiled yet for this workspace. Reports are generated upon completion of full compliance or structural audits.",
              "اس ورک اسپیس کے لیے ابھی تک کوئی باضابطہ رپورٹ جاری نہیں کی گئی۔"
            )}
          </p>
          <Link
            href="/dashboard/reports"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs uppercase tracking-wider transition-all"
          >
            <span>{t("Browse Reports Hub", "رپورٹس ہب کھولیں")}</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}
    </div>
  );
}
