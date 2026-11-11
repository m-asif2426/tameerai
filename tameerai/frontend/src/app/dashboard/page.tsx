"use client";

import { useState, useEffect } from "react";
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
  ChevronRight,
  Layers,
  FolderOpen,
  Scale,
  ShieldAlert,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Project } from "@/types";
import { projectService } from "@/services/projectService";
import { apiClient, ApiUser } from "@/services/apiClient";

export default function DashboardPage() {
  const { t } = useLanguage();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState<ApiUser | null>(() => apiClient.getCachedUser());

  useEffect(() => {
    async function initDashboard() {
      setLoading(true);
      try {
        const [loadedProjects, user] = await Promise.all([
          projectService.getProjects(),
          apiClient.get<ApiUser>("/users/me").catch(() => null),
        ]);
        setProjects(loadedProjects);
        if (user) {
          setCurrentUser(user);
          apiClient.setCachedUser(user);
        }
      } catch (err) {
        console.error("[DashboardOverview] Init error:", err);
      } finally {
        setLoading(false);
      }
    }
    initDashboard();
  }, []);

  const displayName = currentUser?.full_name || "Engineer";

  const getStatusBadge = (status: Project["status"]) => {
    switch (status) {
      case "Active":
        return "bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800";
      case "Under Analysis":
        return "bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800";
      case "Planning":
        return "bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-800";
      default:
        return "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700";
    }
  };

  const getRiskBadge = (risk: Project["risk"]) => {
    switch (risk) {
      case "Low":
        return {
          badge: "bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800",
          dot: "bg-emerald-500",
        };
      case "Medium":
        return {
          badge: "bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800",
          dot: "bg-amber-500",
        };
      case "High":
        return {
          badge: "bg-red-50 dark:bg-red-950/50 text-red-700 dark:text-red-400 border-red-200 dark:border-red-800",
          dot: "bg-red-500 animate-pulse",
        };
      default:
        return {
          badge: "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700",
          dot: "bg-slate-400",
        };
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto font-sans">
      {/* ========================================================= */}
      {/* 1. WELCOME HERO SECTION                                   */}
      {/* ========================================================= */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-navy-900 via-navy-950 to-slate-900 p-6 sm:p-8 lg:p-10 text-white shadow-xl border border-slate-800">
        <div className="absolute top-0 right-0 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/15 text-xs font-semibold text-orange-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>{t("Verified Engine Active • PBC 2021 Loaded", "تصدیق شدہ انجن فعال • پی بی سی 2021 ضوابط منسلک")}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black tracking-tight text-white">
              {t(`Welcome back, ${displayName}`, `خوش آمدید، ${displayName}`)}
            </h1>
            <p className="text-sm sm:text-base text-slate-300 max-w-2xl leading-relaxed">
              {t(
                "Construction intelligence command center: multi-tenant workspace management, statutory building regulations, and canonical material market benchmarks.",
                "تعمیراتی انٹیلی جنس کمانڈ سینٹر: پروجیکٹ مانیٹرنگ، بلڈنگ بائی لاز اور لائیو مارکیٹ ریٹس کا مستند نظام۔"
              )}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <Link
              href="/dashboard/projects"
              className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-orange-500/25 transition-all active:scale-95"
            >
              <PlusCircle className="w-4 h-4" />
              <span>{t("Project Portfolio", "منصوبوں کی فہرست")}</span>
            </Link>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 2. QUICK MODULE ACCESS CARDS                              */}
      {/* ========================================================= */}
      <div>
        <h2 className="text-xs font-black uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-4">
          {t("Core Platform Modules", "پلیٹ فارم کے بنیادی ماڈیولز")}
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Projects */}
          <Link
            href="/dashboard/projects"
            className="group relative p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs hover:shadow-xl hover:border-orange-500/50 transition-all flex flex-col justify-between"
          >
            <div className="w-12 h-12 rounded-xl bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 flex items-center justify-center mb-4 transition-transform group-hover:scale-110">
              <FolderOpen className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-navy-900 dark:text-white group-hover:text-orange-500 transition-colors">
                {t("Project Workspaces", "تعمیراتی ورک اسپیس")}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                {t("Manage blueprints, documents, and BOQ estimates", "نقشہ جات اور لاگت کا انتظام")}
              </p>
            </div>
            <div className="mt-4 flex items-center text-xs font-semibold text-orange-600 dark:text-orange-400 gap-1 group-hover:gap-2 transition-all">
              <span>{t("View Projects", "منصوبے دیکھیں")}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Link>

          {/* Card 2: Structural Safety */}
          <Link
            href="/dashboard/safety"
            className="group relative p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs hover:shadow-xl hover:border-blue-500/50 transition-all flex flex-col justify-between"
          >
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 flex items-center justify-center mb-4 transition-transform group-hover:scale-110">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-navy-900 dark:text-white group-hover:text-blue-500 transition-colors">
                {t("Structural Safety", "سٹرکچرل سیفٹی")}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                {t("38 deterministic life-safety rules and hazard checks", "38 مستند سیفٹی رولز اور تکنیکی جائزے")}
              </p>
            </div>
            <div className="mt-4 flex items-center text-xs font-semibold text-blue-600 dark:text-blue-400 gap-1 group-hover:gap-2 transition-all">
              <span>{t("Evaluate Hazards", "خطرات کا جائزہ")}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Link>

          {/* Card 3: Regulations */}
          <Link
            href="/dashboard/regulations"
            className="group relative p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs hover:shadow-xl hover:border-emerald-500/50 transition-all flex flex-col justify-between"
          >
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 flex items-center justify-center mb-4 transition-transform group-hover:scale-110">
              <Scale className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-navy-900 dark:text-white group-hover:text-emerald-500 transition-colors">
                {t("Statutory Regulations", "عمارتی ضوابط")}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                {t("Pakistan building codes (PBC 2021) & LDA/SBCA bylaws", "پی بی سی 2021 اور مجاز اتھارٹیز کے قوانین")}
              </p>
            </div>
            <div className="mt-4 flex items-center text-xs font-semibold text-emerald-600 dark:text-emerald-400 gap-1 group-hover:gap-2 transition-all">
              <span>{t("Explore Codes", "ضوابط تلاش کریں")}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Link>

          {/* Card 4: Cost Intelligence */}
          <Link
            href="/dashboard/costs"
            className="group relative p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs hover:shadow-xl hover:border-purple-500/50 transition-all flex flex-col justify-between"
          >
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 flex items-center justify-center mb-4 transition-transform group-hover:scale-110">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-navy-900 dark:text-white group-hover:text-purple-500 transition-colors">
                {t("Material Rates", "میٹریل ریٹس")}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                {t("Canonical market rates for steel, cement, bricks & sand", "سٹیل، سیمنٹ اور اینٹوں کے مستند ریٹس")}
              </p>
            </div>
            <div className="mt-4 flex items-center text-xs font-semibold text-purple-600 dark:text-purple-400 gap-1 group-hover:gap-2 transition-all">
              <span>{t("View Rates", "ریٹس دیکھیں")}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Link>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 3. VERIFIED DATA KPIS                                     */}
      {/* ========================================================= */}
      <div>
        <h2 className="text-xs font-black uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-4">
          {t("System Intelligence Indicators", "سسٹم کے تصدیق شدہ اشاریے")}
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Stat 1: Total User Projects */}
          <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                <Building2 className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
                DB Verified
              </span>
            </div>
            <p className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white">
              {loading ? "..." : projects.length}
            </p>
            <p className="text-xs font-bold text-slate-700 dark:text-slate-300 mt-1">
              {t("Active Project Workspaces", "فعال ورک اسپیس")}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {t("Tenant-Isolated Workspaces", "محفوظ پروجیکٹ ریکارڈز")}
            </p>
          </div>

          {/* Stat 2: Safety Rules */}
          <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                Deterministic
              </span>
            </div>
            <p className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white">38</p>
            <p className="text-xs font-bold text-slate-700 dark:text-slate-300 mt-1">
              {t("Structural Damage Indicators", "سٹرکچرل نقص کے اشاریے")}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {t("Life-Safety Rules Active", "جان لیوا خطرات کے قواعد فعال")}
            </p>
          </div>

          {/* Stat 3: Regulatory Codes */}
          <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                <Scale className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
                Statutory
              </span>
            </div>
            <p className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white">13</p>
            <p className="text-xs font-bold text-slate-700 dark:text-slate-300 mt-1">
              {t("Statutory Building Codes", "سرکاری بلڈنگ ضوابط")}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {t("PBC 2021, LDA, SBCA, CDA", "پی بی سی 2021 اور اتھارٹیز")}
            </p>
          </div>

          {/* Stat 4: Material Benchmark Feeds */}
          <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center">
                <TrendingUp className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-50 dark:bg-purple-950 text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-800">
                PBS + Wholesale
              </span>
            </div>
            <p className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white">6</p>
            <p className="text-xs font-bold text-slate-700 dark:text-slate-300 mt-1">
              {t("Canonical Rate Commodities", "بنیادی تعمیراتی اجناس")}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {t("Steel, Cement, Bricks, Sand, Crush", "سٹیل، سیمنٹ، اینٹیں، ریت")}
            </p>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 4. RECENT PROJECTS SECTION (Genuine Data Only)            */}
      {/* ========================================================= */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-navy-900 dark:text-white">
              {t("Recent Projects", "حالیہ منصوبے")}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {t("Authenticated workspaces in your organization", "آپ کی تنظیم کے فعال منصوبے")}
            </p>
          </div>
          <Link
            href="/dashboard/projects"
            className="text-xs font-bold text-orange-500 hover:text-orange-600 transition-colors inline-flex items-center gap-1"
          >
            <span>{t("View All Projects", "تمام منصوبے دیکھیں")}</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 animate-pulse h-48"
              />
            ))}
          </div>
        )}

        {/* Empty state when 0 projects in DB */}
        {!loading && projects.length === 0 && (
          <div className="bg-white dark:bg-navy-900 rounded-3xl p-10 border border-slate-200/90 dark:border-slate-800 text-center max-w-xl mx-auto shadow-sm">
            <FolderOpen className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-bold text-navy-900 dark:text-white mb-1">
              {t("No Construction Projects Created Yet", "ابھی تک کوئی منصوبہ شامل نہیں کیا گیا")}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto mb-6 leading-relaxed">
              {t(
                "Create your first construction workspace to begin tracking building bylaws, cost estimates, and structural safety.",
                "پہلا پروجیکٹ بنائیں تاکہ خودکار بائی لاز اور لاگت کا تجزیہ شروع کیا جا سکے۔"
              )}
            </p>
            <Link
              href="/dashboard/projects"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs uppercase tracking-wider shadow-md shadow-orange-500/20 transition-all"
            >
              <PlusCircle className="w-4 h-4" />
              <span>{t("Create First Project", "پہلا پروجیکٹ بنائیں")}</span>
            </Link>
          </div>
        )}

        {/* Real Project Cards */}
        {!loading && projects.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {projects.slice(0, 3).map((project) => {
              const riskInfo = getRiskBadge(project.risk);
              const statusClass = getStatusBadge(project.status);

              return (
                <div
                  key={project.id}
                  className="group relative bg-white dark:bg-navy-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 p-5 shadow-2xs hover:shadow-xl hover:border-orange-500/40 transition-all duration-300 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 dark:bg-navy-950 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800">
                        {project.id}
                      </span>
                      <span className={cn("text-[11px] font-bold px-2.5 py-0.5 rounded-full border", statusClass)}>
                        {t(project.status, project.statusUrdu)}
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-navy-900 dark:text-white group-hover:text-orange-500 transition-colors line-clamp-1">
                      <Link href={`/dashboard/projects/${project.id}`}>
                        {t(project.name, project.nameUrdu)}
                      </Link>
                    </h3>

                    <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-1">
                      <MapPin className="w-3.5 h-3.5 text-orange-500 flex-shrink-0" />
                      <span>{t(project.location, project.locationUrdu)} ({project.city})</span>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs">
                      <span className="text-slate-400">{t("Budget", "بجٹ")}</span>
                      <span className="font-black text-navy-900 dark:text-white font-mono">
                        PKR {project.budgetCrore.toFixed(1)} Cr
                      </span>
                    </div>
                  </div>

                  <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between gap-3">
                    <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded-full border inline-flex items-center gap-1", riskInfo.badge)}>
                      <span className={cn("w-1.5 h-1.5 rounded-full", riskInfo.dot)} />
                      <span>{t(project.risk, project.riskUrdu)}</span>
                    </span>

                    <Link
                      href={`/dashboard/projects/${project.id}`}
                      className="inline-flex items-center gap-1 text-xs font-bold text-orange-500 hover:text-orange-600 transition-colors"
                    >
                      <span>{t("Open Workspace", "کھولیں")}</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
