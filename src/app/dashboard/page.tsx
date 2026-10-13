"use client";

import { useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  Building2,
  ShieldCheck,
  TrendingUp,
  MessageSquare,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  PlusCircle,
  UploadCloud,
  FileText,
  BarChart3,
  Sparkles,
  MapPin,
  Calendar,
  AlertCircle,
  FileCheck2,
  X,
  Upload,
  ChevronRight,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface ProjectItem {
  id: string;
  name: string;
  nameUrdu: string;
  location: string;
  type: string;
  status: "Active" | "Under Audit" | "Planning";
  statusUrdu: string;
  riskLevel: "Low Risk" | "Medium Risk" | "High Risk";
  riskLevelUrdu: string;
  complianceScore: number;
  lastUpdate: string;
  lastUpdateUrdu: string;
  progress: number;
  budget: string;
  spent: string;
  riskDetails: string;
  riskDetailsUrdu: string;
}

const recentProjects: ProjectItem[] = [
  {
    id: "PRJ-DHA-01",
    name: "DHA Commercial Plaza",
    nameUrdu: "ڈی ایچ اے کمرشل پلازہ",
    location: "Phase 6, Sector G, Lahore",
    type: "Commercial G+12",
    status: "Active",
    statusUrdu: "فعال (Active)",
    riskLevel: "Low Risk",
    riskLevelUrdu: "کم خطرہ (Low Risk)",
    complianceScore: 94,
    lastUpdate: "2 hours ago",
    lastUpdateUrdu: "2 گھنٹے پہلے",
    progress: 68,
    budget: "PKR 180M",
    spent: "PKR 122M",
    riskDetails: "All structural columns and boundary setbacks verified against PBC 2021.",
    riskDetailsUrdu: "تمام سٹرکچرل کالم اور باؤنڈری سیٹ بیکس پی بی سی 2021 کے مطابق تصدیق شدہ۔",
  },
  {
    id: "PRJ-MT-02",
    name: "Model Town House",
    nameUrdu: "ماڈل ٹاؤن ہاؤس",
    location: "Block C, Model Town, Lahore",
    type: "2 Kanal Residential Villa",
    status: "Under Audit",
    statusUrdu: "زیرِ آڈٹ (Under Audit)",
    riskLevel: "Medium Risk",
    riskLevelUrdu: "درمیانہ خطرہ (Medium Risk)",
    complianceScore: 78,
    lastUpdate: "Yesterday",
    lastUpdateUrdu: "کل شام 5:30",
    progress: 42,
    budget: "PKR 45M",
    spent: "PKR 18.5M",
    riskDetails: "Rear setback is 4.5ft vs required 6.0ft in LDA residential bylaws.",
    riskDetailsUrdu: "پچھلا سیٹ بیک 4.5 فٹ ہے جبکہ ایل ڈی اے ضوابط کے تحت 6.0 فٹ لازمی ہے۔",
  },
  {
    id: "PRJ-FAC-03",
    name: "Factory Project",
    nameUrdu: "فیکٹری پروجیکٹ",
    location: "Sundar Industrial Estate, Lahore",
    type: "Industrial Warehouse & Plants",
    status: "Planning",
    statusUrdu: "منصوبہ بندی (Planning)",
    riskLevel: "High Risk",
    riskLevelUrdu: "زیادہ خطرہ (High Risk)",
    complianceScore: 61,
    lastUpdate: "3 days ago",
    lastUpdateUrdu: "3 دن پہلے",
    progress: 15,
    budget: "PKR 95M",
    spent: "PKR 14M",
    riskDetails: "Fire escape corridor width is 3.2ft vs 5.0ft minimum under PBC 2021 Chapter 9.",
    riskDetailsUrdu: "فائر ایسکیپ راہداری 3.2 فٹ ہے جبکہ پی بی سی 2021 باب 9 کے تحت کم از کم 5.0 فٹ لازمی ہے۔",
  },
];

export default function DashboardPage() {
  const { t } = useLanguage();
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const handleSimulateUpload = (e: React.FormEvent) => {
    e.preventDefault();
    setIsUploading(true);
    setTimeout(() => {
      setIsUploading(false);
      setUploadSuccess(true);
      setTimeout(() => {
        setUploadSuccess(false);
        setUploadModalOpen(false);
        setSelectedFile(null);
      }, 1200);
    }, 1500);
  };

  const getStatusBadge = (status: ProjectItem["status"]) => {
    switch (status) {
      case "Active":
        return "bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800";
      case "Under Audit":
        return "bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800";
      case "Planning":
        return "bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-800";
    }
  };

  const getRiskBadge = (risk: ProjectItem["riskLevel"]) => {
    switch (risk) {
      case "Low Risk":
        return {
          badge: "bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800",
          dot: "bg-emerald-500",
        };
      case "Medium Risk":
        return {
          badge: "bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-800",
          dot: "bg-amber-500",
        };
      case "High Risk":
        return {
          badge: "bg-red-50 dark:bg-red-950/50 text-red-600 dark:text-red-400 border-red-200 dark:border-red-800",
          dot: "bg-red-500 animate-pulse",
        };
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* ========================================================= */}
      {/* 1. WELCOME SECTION                                        */}
      {/* ========================================================= */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-navy-900 via-navy-950 to-slate-900 p-6 sm:p-8 lg:p-10 text-white shadow-xl border border-slate-800">
        {/* Ambient background grid & glow */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/15 text-xs font-semibold text-orange-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>{t("AI Engine Active • PBC 2021 Rules Loaded", "اے آئی انجن فعال • پی بی سی 2021 ضوابط لوڈ ہو چکے ہیں")}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black tracking-tight text-white">
              {t("Welcome back, Aslam Bhai", "خوش آمدید، اسلم بھائی 👋")}
            </h1>
            <p className="text-sm sm:text-base text-slate-300 max-w-2xl leading-relaxed">
              {t(
                "Here is your AI construction intelligence command center. You have 3 active projects being monitored with 1 critical fire safety alert pending in Factory Project.",
                "یہ آپ کا اے آئی تعمیراتی کمانڈ سینٹر ہے۔ 3 منصوبوں کی نگرانی جاری ہے، اور فیکٹری پروجیکٹ میں 1 اہم فائر سیفٹی الرٹ پر توجہ درکار ہے۔"
              )}
            </p>
          </div>

          {/* Quick Date & Action */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <Link
              href="/dashboard/compliance?action=new"
              className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-orange-500/25 transition-all active:scale-95"
            >
              <PlusCircle className="w-4 h-4" />
              <span>{t("New Code Audit", "نیا کوڈ آڈٹ")}</span>
            </Link>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 2. QUICK ACTION CARDS                                     */}
      {/* ========================================================= */}
      <div>
        <h2 className="text-xs font-black uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-4">
          {t("Quick Actions", "فوری اقدامات")}
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Create New Audit */}
          <Link
            href="/dashboard/audit"
            className="group relative p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-xl hover:border-orange-500/50 transition-all flex flex-col justify-between"
          >
            <div className="w-12 h-12 rounded-xl bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 flex items-center justify-center mb-4 transition-transform group-hover:scale-110">
              <PlusCircle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-navy-900 dark:text-white group-hover:text-orange-500 transition-colors">
                {t("Create New Audit", "نیا آڈٹ بنائیں")}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                {t("Verify architectural drawings against PBC 2021 bylaws", "نقشے کا بلڈنگ کوڈ کے تحت خودکار آڈٹ کریں")}
              </p>
            </div>
            <div className="mt-4 flex items-center text-xs font-semibold text-orange-600 dark:text-orange-400 gap-1 group-hover:gap-2 transition-all">
              <span>{t("Start Audit", "شروع کریں")}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Link>

          {/* Card 2: Upload Document */}
          <button
            type="button"
            onClick={() => setUploadModalOpen(true)}
            className="group text-left relative p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-xl hover:border-blue-500/50 transition-all flex flex-col justify-between"
          >
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 flex items-center justify-center mb-4 transition-transform group-hover:scale-110">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-navy-900 dark:text-white group-hover:text-blue-500 transition-colors">
                {t("Upload Document", "دستاویز اپ لوڈ کریں")}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                {t("Upload CAD .DWG, blueprint PDFs, or FIDIC contracts", "سی اے ڈی ڈرائنگ، پی ڈی ایف یا معاہدہ اپ لوڈ کریں")}
              </p>
            </div>
            <div className="mt-4 flex items-center text-xs font-semibold text-blue-600 dark:text-blue-400 gap-1 group-hover:gap-2 transition-all">
              <span>{t("Choose Files", "فائل منتخب کریں")}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </button>

          {/* Card 3: Ask AI */}
          <Link
            href="/dashboard/ai-assistant"
            className="group relative p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-xl hover:border-emerald-500/50 transition-all flex flex-col justify-between"
          >
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 flex items-center justify-center mb-4 transition-transform group-hover:scale-110">
              <MessageSquare className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-navy-900 dark:text-white group-hover:text-emerald-500 transition-colors">
                {t("Ask AI", "اے آئی سے پوچھیں")}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                {t("Urdu/English site engineering assistant with code citations", "انجینئرنگ اور سائیٹ کے سوالات کے فوری جوابات")}
              </p>
            </div>
            <div className="mt-4 flex items-center text-xs font-semibold text-emerald-600 dark:text-emerald-400 gap-1 group-hover:gap-2 transition-all">
              <span>{t("Open Chat", "چیٹ کھولیں")}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Link>

          {/* Card 4: View Reports */}
          <Link
            href="/dashboard/reports"
            className="group relative p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-xl hover:border-purple-500/50 transition-all flex flex-col justify-between"
          >
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 flex items-center justify-center mb-4 transition-transform group-hover:scale-110">
              <BarChart3 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-navy-900 dark:text-white group-hover:text-purple-500 transition-colors">
                {t("View Reports", "رپورٹس دیکھیں")}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                {t("Investor & municipal stamped PDF audit compliance summaries", "پی ڈی ایف آڈٹ رپورٹس اور سرٹیفکیٹس ڈاؤن لوڈ کریں")}
              </p>
            </div>
            <div className="mt-4 flex items-center text-xs font-semibold text-purple-600 dark:text-purple-400 gap-1 group-hover:gap-2 transition-all">
              <span>{t("Browse Reports", "رپورٹس دیکھیں")}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Link>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 3. STATISTICS                                             */}
      {/* ========================================================= */}
      <div>
        <h2 className="text-xs font-black uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-4">
          {t("Key Performance Indicators", "اہم اعداد و شمار")}
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Stat 1: Active Projects */}
          <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                <Building2 className="w-5 h-5" />
              </div>
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
                +2 {t("this month", "اس ماہ")}
              </span>
            </div>
            <p className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white">12</p>
            <p className="text-xs font-bold text-slate-700 dark:text-slate-300 mt-1">
              {t("Active Projects", "فعال منصوبے (Active Projects)")}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {t("Lahore, Karachi & Islamabad", "لاہور، کراچی اور اسلام آباد")}
            </p>
          </div>

          {/* Stat 2: Completed Audits */}
          <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                98.4% {t("Pass", "پاس")}
              </span>
            </div>
            <p className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white">48</p>
            <p className="text-xs font-bold text-slate-700 dark:text-slate-300 mt-1">
              {t("Completed Audits", "مکمل آڈٹس (Completed Audits)")}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {t("PBC 2021 & LDA Verified", "پی بی سی اور ایل ڈی اے مصدقہ")}
            </p>
          </div>

          {/* Stat 3: Risk Alerts */}
          <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 text-red-600 dark:text-red-400 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-red-50 dark:bg-red-950 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800 animate-pulse">
                {t("Action Needed", "توجہ درکار")}
              </span>
            </div>
            <p className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white text-red-600 dark:text-red-400">
              3
            </p>
            <p className="text-xs font-bold text-slate-700 dark:text-slate-300 mt-1">
              {t("Risk Alerts", "خطرے کے الرٹس (Risk Alerts)")}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {t("1 Critical setback alert in Factory", "فیکٹری میں 1 اہم سیٹ بیک الرٹ")}
            </p>
          </div>

          {/* Stat 4: Reports */}
          <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center">
                <FileText className="w-5 h-5" />
              </div>
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-purple-50 dark:bg-purple-950 text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-800">
                +18 {t("this week", "اس ہفتے")}
              </span>
            </div>
            <p className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white">156</p>
            <p className="text-xs font-bold text-slate-700 dark:text-slate-300 mt-1">
              {t("Reports", "رپورٹس (Reports)")}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {t("Stamped Official PDF Exports", "مہر شدہ سرکاری پی ڈی ایف فائلز")}
            </p>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 4. RECENT PROJECTS (DHA Plaza, Model Town, Factory)       */}
      {/* ========================================================= */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base sm:text-lg font-black text-navy-900 dark:text-white tracking-tight">
              {t("Recent Projects", "حالیہ منصوبے (Recent Projects)")}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {t("Real-time code audit, risk levels, and progress tracking", "ریئل ٹائم کوڈ آڈٹ، رسک لیول اور پیشرفت کی ٹریکنگ")}
            </p>
          </div>
          <Link
            href="/dashboard/projects"
            className="text-xs font-bold text-orange-600 dark:text-orange-400 hover:underline flex items-center gap-1"
          >
            <span>{t("View All Projects", "تمام منصوبے دیکھیں")}</span>
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>

        {/* 3 Dummy Project Cards */}
        <div className="grid md:grid-cols-3 gap-6">
          {recentProjects.map((project) => {
            const riskConfig = getRiskBadge(project.riskLevel);
            return (
              <div
                key={project.id}
                className="group relative rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800 shadow-sm hover:shadow-xl hover:border-orange-500/40 transition-all p-6 flex flex-col justify-between"
              >
                <div>
                  {/* Top Header: Status & Risk Level */}
                  <div className="flex items-center justify-between gap-2 mb-4">
                    {/* Status badge */}
                    <span
                      className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${getStatusBadge(
                        project.status
                      )}`}
                    >
                      {t(project.status, project.statusUrdu)}
                    </span>

                    {/* Risk Level badge */}
                    <div
                      className={`inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-1 rounded-full border ${riskConfig.badge}`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${riskConfig.dot}`} />
                      <span>{t(project.riskLevel, project.riskLevelUrdu)}</span>
                    </div>
                  </div>

                  {/* Project Title & Location */}
                  <h3 className="text-base font-bold text-navy-900 dark:text-white group-hover:text-orange-500 transition-colors">
                    {t(project.name, project.nameUrdu)}
                  </h3>
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 mt-1 mb-4">
                    <MapPin className="w-3.5 h-3.5 text-orange-500 flex-shrink-0" />
                    <span className="truncate">{project.location}</span>
                  </div>

                  {/* Progress & Compliance Bar */}
                  <div className="space-y-3 p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-100 dark:border-slate-800/80 mb-4">
                    <div>
                      <div className="flex items-center justify-between text-xs font-semibold mb-1">
                        <span className="text-slate-600 dark:text-slate-400">
                          {t("Construction Progress", "تعمیراتی پیشرفت")}
                        </span>
                        <span className="text-navy-900 dark:text-white font-bold">
                          {project.progress}%
                        </span>
                      </div>
                      <div className="h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-orange-500 rounded-full transition-all duration-500"
                          style={{ width: `${project.progress}%` }}
                        />
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-200/50 dark:border-slate-800/60">
                      <span className="text-slate-500 dark:text-slate-400">
                        {t("PBC Compliance Score", "تعمیل کا اسکور")}
                      </span>
                      <span
                        className={cn(
                          "font-black text-xs",
                          project.complianceScore >= 90
                            ? "text-emerald-600 dark:text-emerald-400"
                            : project.complianceScore >= 75
                            ? "text-amber-600 dark:text-amber-400"
                            : "text-red-600 dark:text-red-400"
                        )}
                      >
                        {project.complianceScore}%
                      </span>
                    </div>
                  </div>

                  {/* Risk Details snippet */}
                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed line-clamp-2 mb-4">
                    {t(project.riskDetails, project.riskDetailsUrdu)}
                  </p>
                </div>

                {/* Footer: Last Update & Action */}
                <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <Clock className="w-3.5 h-3.5" />
                    <span>
                      {t("Updated", "اپ ڈیٹ")}: {t(project.lastUpdate, project.lastUpdateUrdu)}
                    </span>
                  </div>
                  <Link
                    href={`/dashboard/projects/${project.id}`}
                    className="font-bold text-orange-600 dark:text-orange-400 hover:text-orange-700 transition-colors inline-flex items-center gap-1"
                  >
                    <span>{t("Open Workspace", "ورک اسپیس کھولیں")}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ========================================================= */}
      {/* MODAL: UPLOAD DOCUMENT POPUP                              */}
      {/* ========================================================= */}
      {uploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/70 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-lg rounded-3xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6 sm:p-8">
            <button
              onClick={() => setUploadModalOpen(false)}
              className="absolute top-5 right-5 p-1.5 rounded-xl text-slate-400 hover:text-navy-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-orange-500/10 text-orange-500 flex items-center justify-center">
                <UploadCloud className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-navy-900 dark:text-white">
                  {t("Upload Construction Document", "تعمیراتی دستاویز اپ لوڈ کریں")}
                </h3>
                <p className="text-xs text-slate-400">
                  {t("Supported formats: CAD (.dwg, .dxf), Blueprint PDF, BOQ (.xlsx)", "معاون فارمیٹس: سی اے ڈی، پی ڈی ایف، بی او کیو")}
                </p>
              </div>
            </div>

            <form onSubmit={handleSimulateUpload} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                  {t("Select Target Project", "پروجیکٹ منتخب کریں")}
                </label>
                <select className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20">
                  <option value="DHA">DHA Commercial Plaza</option>
                  <option value="ModelTown">Model Town House</option>
                  <option value="Factory">Factory Project</option>
                </select>
              </div>

              {/* Drag and Drop Box */}
              <div
                onClick={() => setSelectedFile("DHA-Commercial-Plaza-G12-Structural-Drawings.dwg")}
                className="border-2 border-dashed border-slate-200 dark:border-slate-800 hover:border-orange-500/60 dark:hover:border-orange-500/60 rounded-2xl p-6 text-center cursor-pointer bg-slate-50/50 dark:bg-navy-950/50 transition-all"
              >
                <div className="w-12 h-12 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-400 flex items-center justify-center mx-auto mb-3">
                  <Upload className="w-6 h-6 text-orange-500" />
                </div>
                {selectedFile ? (
                  <div className="text-xs text-emerald-600 dark:text-emerald-400 font-bold flex items-center justify-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>{selectedFile}</span>
                  </div>
                ) : (
                  <>
                    <p className="text-xs font-bold text-navy-900 dark:text-white">
                      {t("Click to choose file or drag and drop here", "فائل منتخب کرنے کے لیے کلک کریں")}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      {t("Auto-triggers dimensional setback & code compliance parser", "خودکار سیٹ بیک اور کوڈ تعمیل چیک ہوگا")}
                    </p>
                  </>
                )}
              </div>

              {uploadSuccess ? (
                <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-emerald-600 dark:text-emerald-400 text-xs font-bold text-center flex items-center justify-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{t("Document Uploaded! Starting AI Audit...", "دستاویز اپ لوڈ ہو گئی! آڈٹ شروع ہو رہا ہے...")}</span>
                </div>
              ) : (
                <button
                  type="submit"
                  disabled={isUploading}
                  className="w-full py-3 rounded-xl font-bold text-xs uppercase tracking-wider text-white bg-orange-500 hover:bg-orange-600 shadow-md shadow-orange-500/20 transition-all flex items-center justify-center gap-2"
                >
                  {isUploading ? (
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      <span>{t("Run Instant AI Audit", "فوری اے آئی آڈٹ چلائیں")}</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              )}
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
