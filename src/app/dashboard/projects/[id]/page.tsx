"use client";

import { useState } from "react";
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
  TrendingDown,
  Cpu,
  Coins,
  Share2,
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

// Project metadata
const projectData = {
  id: "PRJ-001",
  name: "DHA Commercial Plaza",
  nameUrdu: "ڈی ایچ اے کمرشل پلازہ",
  location: "Phase 6, Sector G, Lahore, Pakistan",
  locationUrdu: "فیز 6، سیکٹر جی، لاہور",
  governingAuthority: "DHA Lahore & PBC 2021",
  type: "Commercial G+12 Mixed-Use Plaza",
  typeUrdu: "کمرشل G+12 پلازہ",
  budgetCrore: 12.0,
  spentCrore: 7.2,
  status: "Under Analysis" as const,
  statusUrdu: "زیرِ تجزیہ (Under Analysis)",
  riskLevel: "Medium" as const,
  riskLevelUrdu: "درمیانہ خطرہ (Medium)",
  complianceScore: 84,
  lastUpdate: "2 hours ago",
  lastUpdateUrdu: "2 گھنٹے پہلے",
  floors: 13,
  areaSqft: "45,000 sq ft",
  engineer: "Engr. Tariq Mehmood (Chief Structural Engineer)",
  handoverDate: "December 2024",
};

// Documents list
const projectDocuments = [
  {
    id: "DOC-01",
    name: "DHA-Plaza-G12-Structural-Drawings-Rev4.dwg",
    type: "CAD Drawing",
    size: "42.5 MB",
    uploadedBy: "Engr. Tariq",
    uploadTime: "2 hours ago",
    status: "Verified",
    icon: FileCode,
    color: "text-blue-500",
  },
  {
    id: "DOC-02",
    name: "PBC-2021-Setback-Calculations-Approval.pdf",
    type: "Architectural Blueprint",
    size: "8.4 MB",
    uploadedBy: "Ar. Bilal",
    uploadTime: "Yesterday",
    status: "Verified",
    icon: FileText,
    color: "text-red-500",
  },
  {
    id: "DOC-03",
    name: "Subcontractor-HVAC-FIDIC-Agreement.pdf",
    type: "Legal Contract",
    size: "1.6 MB",
    uploadedBy: "Legal Dept",
    uploadTime: "2 days ago",
    status: "2 Risk Flags",
    icon: FileText,
    color: "text-amber-500",
  },
  {
    id: "DOC-04",
    name: "Master-BOQ-Civil-Works-Estimate.xlsx",
    type: "BOQ Spreadsheet",
    size: "3.2 MB",
    uploadedBy: "Quantity Surveyor",
    uploadTime: "3 days ago",
    status: "Verified",
    icon: FileSpreadsheet,
    color: "text-emerald-500",
  },
  {
    id: "DOC-05",
    name: "Mughal-Steel-Grade60-Mill-Certificate.pdf",
    type: "Material Testing Submittal",
    size: "2.1 MB",
    uploadedBy: "Site Supervisor",
    uploadTime: "5 days ago",
    status: "Approved",
    icon: FileCheck2,
    color: "text-emerald-500",
  },
];

// Recent Activities
const activities = [
  {
    id: "ACT-01",
    title: "Structural Drawing Rev4 Uploaded",
    titleUrdu: "سٹرکچرل ڈرائنگ ریویژن 4 اپ لوڈ کی گئی",
    user: "Engr. Tariq Mehmood",
    time: "2 hours ago",
    type: "upload",
    detail: "Uploaded DHA-Plaza-G12-Structural-Drawings-Rev4.dwg for 7th floor slab audit.",
  },
  {
    id: "ACT-02",
    title: "TameerAI Verified 14 PBC 2021 Bylaws",
    titleUrdu: "TameerAI نے 14 پی بی سی ضوابط کی خودکار تصدیق کی",
    user: "TameerAI Engine",
    time: "4 hours ago",
    type: "ai",
    detail: "Dimensional setback check passed with 84% score. 1 minor clearance flag on rear duct.",
  },
  {
    id: "ACT-03",
    title: "Material Rate Index Synchronized",
    titleUrdu: "لاہور مارکیٹ ریٹس اپ ڈیٹ کیے گئے",
    user: "Cost Intelligence",
    time: "Yesterday at 4:15 PM",
    type: "cost",
    detail: "Mughal Steel Grade 60 adjusted to PKR 285k/ton. Cement stable at PKR 1,150/bag.",
  },
  {
    id: "ACT-04",
    title: "Contract Risk Alert Flagged",
    titleUrdu: "معاہدے میں تاخیر کے جرمانے کا الرٹ",
    user: "Contract Analyzer",
    time: "2 days ago",
    type: "contract",
    detail: "Uncapped delay penalty clause detected in Subcontractor HVAC agreement.",
  },
];

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
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("overview");

  // Chat message state for AI Chat tab
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([
    {
      sender: "bot",
      text: "Hello Aslam Bhai! I am TameerAI's dedicated project assistant for DHA Commercial Plaza. How can I help you check building codes, contract clauses, or material estimates today?",
      urduText: "السلام علیکم اسلم بھائی! میں ڈی ایچ اے کمرشل پلازہ کا مخصوص اے آئی اسسٹنٹ ہوں۔ آج میں بلڈنگ کوڈز، معاہدے کی شقوں یا لاگت کے تخمینے میں کس طرح مدد کروں؟",
      time: "10:30 AM",
    },
    {
      sender: "user",
      text: "What is the status of the 7th floor slab compliance under PBC 2021?",
      time: "10:32 AM",
    },
    {
      sender: "bot",
      text: "Based on Rev4 drawings: Column rebar ratio is 2.8% (fully compliant with PBC 2021 Chapter 5 seismic criteria). Concrete cover of 1.5 inches satisfies fire rating bylaws. Only rear service duct needs an extra 4 inches clearance.",
      urduText: "ریویژن 4 ڈرائنگ کے مطابق: کالم سٹیل تناسب 2.8% ہے جو پی بی سی 2021 زلزلہ معیار کے مطابق ہے۔ کنکریٹ کور 1.5 انچ فائر سیفٹی معیار پر پورا اترتا ہے۔ صرف پچھلی سروس ڈکٹ کو 4 انچ مزید فاصلہ درکار ہے۔",
      time: "10:32 AM",
    },
  ]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMsg = { sender: "user", text: chatInput, time: "Just now" };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput("");

    setTimeout(() => {
      const aiReply = {
        sender: "bot",
        text: `Regarding DHA Commercial Plaza: TameerAI verified this against PBC 2021 Section 4.2. All dimensions and rebar specifications have been cross-checked.`,
        urduText: `ڈی ایچ اے کمرشل پلازہ کے حوالے سے: TameerAI نے پی بی سی 2021 سیکشن 4.2 کے مطابق تصدیق کی ہے۔ تمام پیمائشیں منظور شدہ ہیں۔`,
        time: "Just now",
      };
      setChatMessages((prev) => [...prev, aiReply]);
    }, 1000);
  };

  const tabs: { key: WorkspaceTab; labelEn: string; labelUr: string; icon: React.ComponentType<{ className?: string }>; count?: number }[] = [
    { key: "overview", labelEn: "Overview", labelUr: "خلاصہ (Overview)", icon: Layers },
    { key: "ai-chat", labelEn: "AI Chat", labelUr: "اے آئی چیٹ (AI Chat)", icon: MessageSquare, count: 3 },
    { key: "documents", labelEn: "Documents", labelUr: "دستاویزات (Documents)", icon: FolderOpen, count: 5 },
    { key: "compliance", labelEn: "Compliance", labelUr: "تعمیل (Compliance)", icon: ShieldCheck, count: 14 },
    { key: "contract", labelEn: "Contract", labelUr: "معاہدہ (Contract)", icon: FileText, count: 2 },
    { key: "cost", labelEn: "Cost", labelUr: "لاگت (Cost)", icon: Coins },
    { key: "reports", labelEn: "Reports", labelUr: "رپورٹس (Reports)", icon: FileCheck2, count: 4 },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in">
      {/* ========================================================= */}
      {/* 1. TOP BREADCRUMB                                         */}
      {/* ========================================================= */}
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <Link
          href="/dashboard/projects"
          className="hover:text-orange-500 transition-colors font-medium"
        >
          {t("My Projects", "میرے منصوبے")}
        </Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-navy-900 dark:text-white font-bold">
          {projectData.name}
        </span>
        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
          {projectData.id}
        </span>
      </div>

      {/* ========================================================= */}
      {/* 2. TOP SECTION: Project Name, Location, Budget, Status    */}
      {/* ========================================================= */}
      <div className="rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-slate-100 dark:border-slate-800/80">
          {/* Left: Project Name + Location */}
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white tracking-tight">
                {t(projectData.name, projectData.nameUrdu)}
              </h1>

              {/* Status Badge */}
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800 inline-flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                <span>{t(projectData.status, projectData.statusUrdu)}</span>
              </span>

              {/* Risk Badge */}
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800 inline-flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                <span>{t(projectData.riskLevel, projectData.riskLevelUrdu)} {t("Risk", "خطرہ")}</span>
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
              <span className="flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-orange-500 flex-shrink-0" />
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  {t(projectData.location, projectData.locationUrdu)}
                </span>
              </span>
              <span className="flex items-center gap-1.5">
                <Building2 className="w-4 h-4 text-slate-400 flex-shrink-0" />
                <span>{t(projectData.type, projectData.typeUrdu)}</span>
              </span>
              <span className="flex items-center gap-1.5">
                <HardHat className="w-4 h-4 text-slate-400 flex-shrink-0" />
                <span>{projectData.engineer}</span>
              </span>
            </div>
          </div>

          {/* Right: Quick Action Buttons (Autodesk Construction style) */}
          <div className="flex items-center gap-2.5 self-start lg:self-auto flex-wrap">
            <button
              onClick={() => setActiveTab("ai-chat")}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs uppercase tracking-wider shadow-md shadow-orange-500/20 transition-all active:scale-95"
            >
              <Sparkles className="w-4 h-4" />
              <span>{t("Ask AI Assistant", "اے آئی سے پوچھیں")}</span>
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

        {/* Metric Bar in Top Section: Budget, Spent, Compliance, Handover */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6">
          {/* Budget */}
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              {t("Total Approved Budget", "کل منظور شدہ بجٹ")}
            </span>
            <div className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white mt-0.5">
              PKR {projectData.budgetCrore.toFixed(1)} {t("Crore", "کروڑ")}
            </div>
            <span className="text-[11px] text-slate-400">
              {t("Spent: PKR", "خرچ ہوا: PKR")} {projectData.spentCrore.toFixed(1)} {t("Cr (60%)", "کروڑ (60%)")}
            </span>
          </div>

          {/* PBC Compliance Score */}
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              {t("PBC 2021 Compliance", "پی بی سی 2021 تعمیل")}
            </span>
            <div className="text-xl sm:text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-0.5 flex items-center gap-1.5">
              <span>{projectData.complianceScore}%</span>
              <ShieldCheck className="w-5 h-5 text-emerald-500" />
            </div>
            <span className="text-[11px] text-slate-400">
              {t("14 Bylaws Checked • 1 Notice", "14 ضوابط تصدیق شدہ")}
            </span>
          </div>

          {/* Construction Progress */}
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              {t("Physical Progress", "تعمیراتی پیشرفت")}
            </span>
            <div className="text-xl sm:text-2xl font-black text-orange-500 mt-0.5">
              68%
            </div>
            <span className="text-[11px] text-slate-400">
              {t("7th Floor Slab Poured", "ساتویں منزل کی چھت مکمل")}
            </span>
          </div>

          {/* Target Handover */}
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              {t("Target Handover", "تکمیل کی تاریخ")}
            </span>
            <div className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white mt-0.5">
              {projectData.handoverDate}
            </div>
            <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold">
              {t("On Schedule (0 days delay)", "بر وقت (شیڈول کے مطابق)")}
            </span>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 3. TABS NAVIGATION (Autodesk Construction Cloud Style)     */}
      {/* ========================================================= */}
      <div className="border-b border-slate-200 dark:border-slate-800 overflow-x-auto scrollbar-none">
        <div className="flex items-center gap-2 min-w-max pb-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.key;

            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={cn(
                  "flex items-center gap-2 px-4 py-3 rounded-xl text-xs font-bold transition-all relative",
                  isActive
                    ? "bg-white dark:bg-navy-900 text-orange-600 dark:text-orange-400 shadow-sm border border-slate-200 dark:border-slate-800"
                    : "text-slate-500 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white hover:bg-slate-100/60 dark:hover:bg-slate-800/40"
                )}
              >
                <Icon className={cn("w-4 h-4", isActive ? "text-orange-500" : "text-slate-400")} />
                <span>{t(tab.labelEn, tab.labelUr)}</span>
                {tab.count !== undefined && (
                  <span
                    className={cn(
                      "px-1.5 py-0.2 rounded-md text-[10px] font-bold",
                      isActive
                        ? "bg-orange-100 dark:bg-orange-950 text-orange-600 dark:text-orange-400"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"
                    )}
                  >
                    {tab.count}
                  </span>
                )}
                {isActive && (
                  <div className="absolute bottom-0 left-3 right-3 h-0.5 bg-orange-500 rounded-full" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* ========================================================= */}
      {/* 4. TAB CONTENTS                                           */}
      {/* ========================================================= */}

      {/* --------------------------------------------------------- */}
      {/* TAB A: OVERVIEW (Requested specifically by User)          */}
      {/* --------------------------------------------------------- */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Row 1: Project Progress & Risk Summary */}
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Project Progress Card */}
            <div className="lg:col-span-2 rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800 p-6 sm:p-7 shadow-sm">
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-orange-500/10 text-orange-500 flex items-center justify-center">
                    <TrendingUp className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-navy-900 dark:text-white">
                      {t("Project Progress & Construction Milestones", "پروجیکٹ کی پیشرفت و سنگ میل")}
                    </h2>
                    <p className="text-xs text-slate-400">
                      {t("G+12 Commercial Plaza • Overall 68% complete", "G+12 کمرشل پلازہ • مجموعی طور پر 68% مکمل")}
                    </p>
                  </div>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-orange-100 dark:bg-orange-950 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-800">
                  68% {t("Overall", "مجموعی")}
                </span>
              </div>

              {/* Progress Milestones Bar */}
              <div className="space-y-4">
                {/* Milestone 1 */}
                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1.5">
                    <span className="text-slate-700 dark:text-slate-300">
                      1. {t("Substructure & Deep Piling Foundation (3 Basement levels)", "فاؤنڈیشن اور پائلنگ (3 تہہ خانے)")}
                    </span>
                    <span className="text-emerald-600 font-bold">100% {t("Completed", "مکمل")}</span>
                  </div>
                  <div className="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: "100%" }} />
                  </div>
                </div>

                {/* Milestone 2 */}
                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1.5">
                    <span className="text-slate-700 dark:text-slate-300">
                      2. {t("Superstructure RCC Frame (Ground to 7th Floor)", "سٹرکچر آر سی سی فریم (گراؤنڈ تا 7ویں منزل)")}
                    </span>
                    <span className="text-orange-500 font-bold">85% {t("In Progress", "جاری ہے")}</span>
                  </div>
                  <div className="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-orange-500 rounded-full" style={{ width: "85%" }} />
                  </div>
                </div>

                {/* Milestone 3 */}
                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1.5">
                    <span className="text-slate-700 dark:text-slate-300">
                      3. {t("MEP Plumbing, Electrical & Fire Suppression conduits", "بجلی، پلمبنگ اور فائر سیفٹی سسٹم")}
                    </span>
                    <span className="text-slate-500 font-bold">45%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full" style={{ width: "45%" }} />
                  </div>
                </div>

                {/* Milestone 4 */}
                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1.5">
                    <span className="text-slate-700 dark:text-slate-300">
                      4. {t("Curtain Wall Glazing & Exterior Façade", "بیرونی شیشہ اور فساڈ")}
                    </span>
                    <span className="text-slate-500 font-bold">20%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-purple-500 rounded-full" style={{ width: "20%" }} />
                  </div>
                </div>
              </div>

              {/* Budget consumption ticker */}
              <div className="mt-6 pt-5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                <span className="text-slate-500">
                  {t("Cashflow Burn: PKR 1.2 Crore / month", "ماہانہ لاگت اخراجات: 1.2 کروڑ")}
                </span>
                <span className="text-emerald-600 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {t("All contractor payment certificates verified", "تمام ادائیگی سرٹیفکیٹس تصدیق شدہ")}
                </span>
              </div>
            </div>

            {/* Risk Summary Card */}
            <div className="rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800 p-6 sm:p-7 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center">
                      <AlertTriangle className="w-4 h-4" />
                    </div>
                    <h2 className="text-sm font-bold text-navy-900 dark:text-white">
                      {t("Risk Summary", "رسک سمری (Risk Summary)")}
                    </h2>
                  </div>
                  <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-100 dark:bg-amber-950 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
                    {t("Score: 78/100", "اسکور: 78/100")}
                  </span>
                </div>

                <div className="space-y-3">
                  <div className="p-3 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/70 dark:border-amber-900/40">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-xs font-bold text-navy-900 dark:text-white">
                          {t("Rear Setback Margin", "پچھلا سیٹ بیک مارجن")}
                        </p>
                        <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5 leading-relaxed">
                          {t(
                            "North-East service shaft is within 0.8ft of boundary margin. Approval waiver advised.",
                            "نارتھ ایسٹ ڈکٹ باؤنڈری مارجن سے 0.8 فٹ کے فاصلے پر ہے۔ این او سی درکار ہے۔"
                          )}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-blue-50/60 dark:bg-blue-950/20 border border-blue-200/70 dark:border-blue-900/40">
                    <div className="flex items-start gap-2">
                      <FileText className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-xs font-bold text-navy-900 dark:text-white">
                          {t("FIDIC Penalty Escalation", "معاہدے میں جرمانے کی شق")}
                        </p>
                        <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5 leading-relaxed">
                          {t(
                            "Subcontractor agreement lacks price ceiling for imported chillers.",
                            "ایئر کنڈیشننگ کے ذیلی معاہدے میں قیمت کی حد مقرر نہیں۔"
                          )}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-200/70 dark:border-emerald-900/40">
                    <div className="flex items-start gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-xs font-bold text-navy-900 dark:text-white">
                          {t("Fire Exit & Stairwell Cleared", "فائر سیفٹی و سیڑھیاں منظور")}
                        </p>
                        <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5">
                          {t("PBC 2021 Chapter 9 criteria 100% verified.", "پی بی سی 2021 باب 9 مکمل منظور۔")}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setActiveTab("compliance")}
                className="mt-4 w-full py-2.5 rounded-xl bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-xs font-bold text-navy-900 dark:text-white flex items-center justify-center gap-1.5 transition-colors"
              >
                <span>{t("Review Full Risk Audit", "مکمل رسک آڈٹ دیکھیں")}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Row 2: Uploaded Documents & Recent Activity */}
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Uploaded Documents Preview Card */}
            <div className="rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800 p-6 sm:p-7 shadow-sm">
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center">
                    <FolderOpen className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-navy-900 dark:text-white">
                      {t("Uploaded Documents", "اپ لوڈ کردہ دستاویزات (Uploaded Documents)")}
                    </h2>
                    <p className="text-xs text-slate-400">
                      {t("5 files attached to DHA Commercial Plaza", "ڈی ایچ اے پلازہ سے منسلک 5 اہم فائلز")}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setActiveTab("documents")}
                  className="text-xs font-bold text-orange-600 dark:text-orange-400 hover:underline"
                >
                  {t("View All", "سب دیکھیں")} →
                </button>
              </div>

              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {projectDocuments.slice(0, 4).map((doc) => {
                  const Icon = doc.icon;
                  return (
                    <div
                      key={doc.id}
                      className="py-3 flex items-center justify-between hover:bg-slate-50/60 dark:hover:bg-navy-800/40 rounded-xl px-2 transition-colors"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-9 h-9 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center flex-shrink-0">
                          <Icon className={cn("w-4 h-4", doc.color)} />
                        </div>
                        <div className="min-w-0">
                          <p className="text-xs font-bold text-navy-900 dark:text-white truncate">
                            {doc.name}
                          </p>
                          <p className="text-[11px] text-slate-400 mt-0.5">
                            {doc.type} • {doc.size}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                          {doc.status}
                        </span>
                        <button
                          title="Download Document"
                          className="p-1.5 rounded-lg text-slate-400 hover:text-orange-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                        >
                          <Download className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Recent Activity Card */}
            <div className="rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800 p-6 sm:p-7 shadow-sm">
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-purple-500/10 text-purple-500 flex items-center justify-center">
                    <Clock className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-navy-900 dark:text-white">
                      {t("Recent Activity", "حالیہ سرگرمیاں (Recent Activity)")}
                    </h2>
                    <p className="text-xs text-slate-400">
                      {t("Audit events and structural changes timeline", "آڈٹ اور تبدیلیوں کی تاریخ")}
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                {activities.map((act) => (
                  <div key={act.id} className="flex items-start gap-3">
                    <div className="w-2 h-2 rounded-full bg-orange-500 mt-2 flex-shrink-0 ring-4 ring-orange-500/10" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-baseline justify-between gap-2">
                        <p className="text-xs font-bold text-navy-900 dark:text-white">
                          {t(act.title, act.titleUrdu)}
                        </p>
                        <span className="text-[10px] text-slate-400 whitespace-nowrap">
                          {act.time}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 leading-relaxed">
                        {act.detail}
                      </p>
                      <span className="text-[10px] text-slate-400 font-medium">
                        By {act.user}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------- */}
      {/* TAB B: AI CHAT (Embedded Project Chatbot)                 */}
      {/* --------------------------------------------------------- */}
      {activeTab === "ai-chat" && (
        <div className="rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800 shadow-sm overflow-hidden flex flex-col h-[600px]">
          {/* Chat Header */}
          <div className="p-4 bg-slate-50 dark:bg-navy-950 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-orange-500 text-white flex items-center justify-center shadow-xs">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-navy-900 dark:text-white">
                  TameerAI Project Assistant ({projectData.name})
                </h3>
                <p className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  PBC 2021 Knowledge Base Loaded
                </p>
              </div>
            </div>
            <span className="text-[10px] px-2.5 py-1 rounded-full bg-orange-100 dark:bg-orange-950 text-orange-600 dark:text-orange-400 font-bold">
              English &amp; اردو
            </span>
          </div>

          {/* Messages Feed */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-slate-50/40 dark:bg-navy-950/40">
            {chatMessages.map((msg, i) => (
              <div
                key={i}
                className={cn(
                  "flex items-start gap-2.5 max-w-xl",
                  msg.sender === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
                )}
              >
                <div
                  className={cn(
                    "w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-bold",
                    msg.sender === "user"
                      ? "bg-navy-900 text-white dark:bg-slate-700"
                      : "bg-orange-500 text-white"
                  )}
                >
                  {msg.sender === "user" ? "AB" : <Bot className="w-4 h-4" />}
                </div>
                <div
                  className={cn(
                    "p-3.5 rounded-2xl text-xs leading-relaxed",
                    msg.sender === "user"
                      ? "bg-orange-500 text-white rounded-tr-xs"
                      : "bg-white dark:bg-navy-900 text-navy-900 dark:text-white border border-slate-200 dark:border-slate-800 rounded-tl-xs shadow-2xs"
                  )}
                >
                  <p>{t(msg.text, msg.urduText || msg.text)}</p>
                  <span
                    className={cn(
                      "text-[9px] block text-right mt-1 font-medium",
                      msg.sender === "user" ? "text-orange-200" : "text-slate-400"
                    )}
                  >
                    {msg.time}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Chat Input */}
          <form onSubmit={handleSendMessage} className="p-3 bg-white dark:bg-navy-900 border-t border-slate-200 dark:border-slate-800 flex items-center gap-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder={t(
                "Ask a question about DHA Commercial Plaza codes, drawings, or costs...",
                "ڈی ایچ اے پلازہ کے کوڈز، ڈرائنگ یا اخراجات کے بارے میں سوال پوچھیں..."
              )}
              className="flex-1 px-4 py-2.5 text-xs rounded-xl bg-slate-100 dark:bg-navy-950 border border-transparent focus:border-orange-500 focus:outline-none text-navy-900 dark:text-white"
            />
            <button
              type="submit"
              className="px-4 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white text-xs font-bold transition-colors flex items-center gap-1.5 shadow-xs"
            >
              <span>{t("Send", "ارسال")}</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      )}

      {/* --------------------------------------------------------- */}
      {/* TAB C: DOCUMENTS (Autodesk Style File Manager)            */}
      {/* --------------------------------------------------------- */}
      {activeTab === "documents" && (
        <div className="rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800 p-6 sm:p-7 shadow-sm space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h2 className="text-lg font-bold text-navy-900 dark:text-white">
                {t("Project Files & Engineering Drawings", "پروجیکٹ ڈرائنگز و دستاویزات")}
              </h2>
              <p className="text-xs text-slate-400">
                {t("Centralized repository for CAD (.dwg), PDF blueprints, and contractual submittals.", "سی اے ڈی ڈرائنگز اور پی ڈی ایف دستاویزات کا محفوظ ذخیرہ۔")}
              </p>
            </div>
            <button className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs uppercase tracking-wider shadow-sm transition-colors self-start sm:self-auto">
              <UploadCloud className="w-4 h-4" />
              <span>{t("Upload New File", "نئی فائل اپ لوڈ کریں")}</span>
            </button>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {projectDocuments.map((doc) => {
              const Icon = doc.icon;
              return (
                <div key={doc.id} className="py-4 flex items-center justify-between hover:bg-slate-50/60 dark:hover:bg-navy-800/40 rounded-xl px-3 transition-colors">
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center flex-shrink-0">
                      <Icon className={cn("w-5 h-5", doc.color)} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-navy-900 dark:text-white truncate">
                        {doc.name}
                      </p>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        {doc.type} • {doc.size} • Uploaded by {doc.uploadedBy} ({doc.uploadTime})
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0 ml-4">
                    <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                      {doc.status}
                    </span>
                    <button className="px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 flex items-center gap-1.5 transition-colors">
                      <Download className="w-3.5 h-3.5" />
                      <span>{t("Download", "ڈاؤن لوڈ")}</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* --------------------------------------------------------- */}
      {/* TAB D: COMPLIANCE (PBC 2021 Clause Audit)                 */}
      {/* --------------------------------------------------------- */}
      {activeTab === "compliance" && (
        <div className="rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800 p-6 sm:p-7 shadow-sm space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h2 className="text-lg font-bold text-navy-900 dark:text-white">
                {t("PBC 2021 Building Code Compliance Audit", "پی بی سی 2021 بلڈنگ کوڈ آڈٹ")}
              </h2>
              <p className="text-xs text-slate-400">
                {t("Automated regulatory review against Pakistan Building Code 2021 & LDA bylaws.", "پاکستان بلڈنگ کوڈ 2021 کے مطابق خودکار معائنہ۔")}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-600 border border-emerald-200">
                Score: 84%
              </span>
            </div>
          </div>

          <div className="space-y-3">
            {[
              {
                clause: "PBC 2021 Sec. 4.1 — Front Setback Clearance",
                status: "Pass",
                color: "text-emerald-600 bg-emerald-50 border-emerald-200",
                desc: "30.0 ft front setback verified. Meets commercial high-rise standard.",
              },
              {
                clause: "PBC 2021 Sec. 4.4 — Rear Service Duct Setback",
                status: "Warning",
                color: "text-amber-600 bg-amber-50 border-amber-200",
                desc: "Service duct margin is 5.2 ft vs 6.0 ft recommended for LDA G+12 plazas.",
              },
              {
                clause: "PBC 2021 Ch. 9 — Fire Stairwell Pressurization",
                status: "Pass",
                color: "text-emerald-600 bg-emerald-50 border-emerald-200",
                desc: "Two pressurized fire egress staircases with 2-hour fire-rated doors confirmed.",
              },
              {
                clause: "PBC 2021 Sec. 5.3 — Seismic Zone 2B Column Detailing",
                status: "Pass",
                color: "text-emerald-600 bg-emerald-50 border-emerald-200",
                desc: "Grade 60 ductile ties spaced at 4 inches within column plastic hinge zones.",
              },
            ].map((c, i) => (
              <div key={i} className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-bold text-navy-900 dark:text-white">{c.clause}</p>
                  <p className="text-xs text-slate-500 mt-1">{c.desc}</p>
                </div>
                <span className={cn("px-2.5 py-0.5 rounded-full text-xs font-bold border", c.color)}>
                  {c.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* --------------------------------------------------------- */}
      {/* TAB E: CONTRACT (FIDIC Subcontractor Analyzer)            */}
      {/* --------------------------------------------------------- */}
      {activeTab === "contract" && (
        <div className="rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800 p-6 sm:p-7 shadow-sm space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h2 className="text-lg font-bold text-navy-900 dark:text-white">
                {t("Contract Risk & FIDIC Clause Analysis", "معاہدہ و قانونی خطرات کا تجزیہ")}
              </h2>
              <p className="text-xs text-slate-400">
                {t("Scanned subcontractor & supplier agreements for liability traps.", "ذیلی ٹھیکیداروں کے معاہدات میں پوشیدہ خطرات کی نشاندہی۔")}
              </p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-600 border border-amber-200">
              2 Red Flags Detected
            </span>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/70">
              <h4 className="text-xs font-bold text-amber-900 dark:text-amber-200">
                {t("Clause 8.7: Delay Liquidated Damages", "شق 8.7: تاخیر پر جرمانہ")}
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                {t("Uncapped liability penalty of PKR 50,000 / day without force majeure exemption. Cap at 10% recommended.", "تاخیر کے جرمانے کی کوئی حد مقرر نہیں ہے۔")}
              </p>
            </div>
            <div className="p-4 rounded-xl bg-blue-50/50 dark:bg-blue-950/20 border border-blue-200/70">
              <h4 className="text-xs font-bold text-blue-900 dark:text-blue-200">
                {t("Clause 13.8: Material Price Escalation", "شق 13.8: میٹریل ریٹ اضافہ")}
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                {t("No fixed indexation to Pakistan Bureau of Statistics steel index. Recommend indexing to Lahore market.", "سٹیل ریٹس کی انڈیکسنگ لاہور منڈی سے جوڑنے کی سفارش۔")}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------- */}
      {/* TAB F: COST (Real-Time Rates & BOQ Variance)              */}
      {/* --------------------------------------------------------- */}
      {activeTab === "cost" && (
        <div className="rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800 p-6 sm:p-7 shadow-sm space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h2 className="text-lg font-bold text-navy-900 dark:text-white">
                {t("Cost Intelligence & BOQ Performance", "لاگت انٹیلی جنس و بی او کیو")}
              </h2>
              <p className="text-xs text-slate-400">
                {t("Projected vs Actual spend with live Lahore market rate impact.", "اصل بمقابلہ تخمینی اخراجات اور لائیو مارکیٹ ریٹس۔")}
              </p>
            </div>
            <span className="text-xs font-bold text-emerald-600">
              {t("Within Budget (-3.4% variance)", "بجٹ کے اندر")}
            </span>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800">
              <span className="text-[10px] font-bold uppercase text-slate-400">{t("Steel Consumption", "سٹیل استعمال")}</span>
              <p className="text-lg font-bold text-navy-900 dark:text-white mt-1">420 Tons</p>
              <span className="text-xs text-slate-500">PKR 285k/ton (Mughal Grade 60)</span>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800">
              <span className="text-[10px] font-bold uppercase text-slate-400">{t("Cement Consumption", "سیمنٹ استعمال")}</span>
              <p className="text-lg font-bold text-navy-900 dark:text-white mt-1">18,500 Bags</p>
              <span className="text-xs text-slate-500">PKR 1,150/bag (Lucky OPC 53)</span>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800">
              <span className="text-[10px] font-bold uppercase text-slate-400">{t("Bricks Laid", "اینٹیں استعمال")}</span>
              <p className="text-lg font-bold text-navy-900 dark:text-white mt-1">320,000 Pcs</p>
              <span className="text-xs text-slate-500">PKR 18.5k/1,000 pcs (A-Quality)</span>
            </div>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------- */}
      {/* TAB G: REPORTS (Certified PDF Audits)                     */}
      {/* --------------------------------------------------------- */}
      {activeTab === "reports" && (
        <div className="rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800 p-6 sm:p-7 shadow-sm space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h2 className="text-lg font-bold text-navy-900 dark:text-white">
                {t("Generated Audit Reports for DHA Plaza", "ڈی ایچ اے پلازہ کی آڈٹ رپورٹس")}
              </h2>
              <p className="text-xs text-slate-400">
                {t("Stamped and certified PDF reports ready for bank & municipal submission.", "بینکوں اور اتھارٹیز کے لیے تصدیق شدہ پی ڈی ایف رپورٹس۔")}
              </p>
            </div>
            <button className="px-4 py-2 rounded-xl bg-orange-500 text-white font-bold text-xs uppercase tracking-wider">
              {t("Generate New Report", "نئی رپورٹ بنائیں")}
            </button>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-navy-900 dark:text-white">
                  DHA-Plaza-PBC2021-Compliance-Certificate.pdf
                </p>
                <p className="text-[11px] text-slate-400 mt-0.5">2.4 MB • Stamped 2 hours ago</p>
              </div>
              <button className="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-navy-800 text-xs font-bold hover:bg-orange-500 hover:text-white transition-colors">
                {t("Download", "ڈاؤن لوڈ")}
              </button>
            </div>
            <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-navy-900 dark:text-white">
                  Executive-BOQ-Cost-Variance-Audit.pdf
                </p>
                <p className="text-[11px] text-slate-400 mt-0.5">1.8 MB • Generated Yesterday</p>
              </div>
              <button className="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-navy-800 text-xs font-bold hover:bg-orange-500 hover:text-white transition-colors">
                {t("Download", "ڈاؤن لوڈ")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
