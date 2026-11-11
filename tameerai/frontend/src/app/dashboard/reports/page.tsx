"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  FileText,
  Download,
  Eye,
  ShieldCheck,
  Scale,
  Coins,
  Search,
  Filter,
  Plus,
  Calendar,
  Building2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Sparkles,
  Printer,
  Share2,
  X,
  FileCheck,
  ChevronRight,
  ExternalLink,
  Bot,
  FolderOpen,
  PlusCircle,
  RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { projectService } from "@/services/projectService";
import { reportService, ReportItem } from "@/services/reportService";
import { Project } from "@/types";

export default function ReportsPage() {
  const { t, language } = useLanguage();

  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [activeCategory, setActiveCategory] = useState<"all" | "compliance" | "contract" | "cost">("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Preview Modal
  const [previewReport, setPreviewReport] = useState<ReportItem | null>(null);

  const loadReports = useCallback(async (projId: string, category: string) => {
    if (!projId) {
      setReports([]);
      return;
    }
    setLoading(true);
    try {
      const data = await reportService.getReports(projId, category);
      setReports(data);
    } catch (err) {
      console.error("[ReportsPage] Error loading reports:", err);
      setReports([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load projects on mount
  useEffect(() => {
    async function loadProjects() {
      setLoading(true);
      try {
        const projs = await projectService.getProjects();
        setProjects(projs);
        if (projs.length > 0) {
          const firstId = projs[0].id;
          setSelectedProjectId(firstId);
          await loadReports(firstId, activeCategory);
        }
      } catch (err) {
        console.error("[ReportsPage] Error loading projects:", err);
      } finally {
        setLoading(false);
      }
    }
    loadProjects();
  }, [loadReports, activeCategory]);

  const handleProjectChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const projId = e.target.value;
    setSelectedProjectId(projId);
    await loadReports(projId, activeCategory);
  };

  const handleCategoryChange = async (cat: "all" | "compliance" | "contract" | "cost") => {
    setActiveCategory(cat);
    if (selectedProjectId) {
      await loadReports(selectedProjectId, cat);
    }
  };

  // Filtered reports
  const filteredReports = reports.filter((rpt) => {
    const matchesSearch =
      !searchQuery ||
      rpt.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (rpt.id && rpt.id.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (rpt.author && rpt.author.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesSearch;
  });

  return (
    <div className="space-y-6 pb-12 font-sans">
      {/* ========================================================================= */}
      {/* TOP HEADER & TITLE                                                        */}
      {/* ========================================================================= */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20">
              {t("Executive Engineering Dossiers", "انجینئرنگ اور قانونی دستاویزات")}
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {t("PBC 2021 & FIDIC Standards", "پی بی سی 2021 اور فڈک معیارات")}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white tracking-tight flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-orange-500" />
            <span>{t("Reports Management", "رپورٹس مینجمنٹ (Reports Management)")}</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {t(
              "Access and manage verified engineering compliance certificates, FIDIC contract risk evaluations, and financial cost intelligence dossiers.",
              "کلائنٹس اور اتھارٹیز کے لیے تصدیق شدہ پی بی سی 2021، قانونی معاہدات اور لاگت رپورٹس دیکھیں۔"
            )}
          </p>
        </div>

        {/* Project Selector & Actions */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 px-3 py-1.5 rounded-xl shadow-2xs">
            <Building2 className="w-4 h-4 text-orange-500" />
            <select
              value={selectedProjectId}
              onChange={handleProjectChange}
              className="bg-transparent text-xs font-bold text-slate-800 dark:text-slate-200 focus:outline-none"
              disabled={projects.length === 0}
            >
              {projects.length === 0 ? (
                <option value="">{t("No Projects in DB", "کوئی پروجیکٹ نہیں")}</option>
              ) : (
                projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.code || p.id.slice(0, 8)})
                  </option>
                ))
              )}
            </select>
          </div>

          <Link
            href="/dashboard/audit"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 text-white shadow-sm transition-all"
          >
            <RefreshCw className="w-4 h-4" />
            <span>{t("Generate from Audit", "آڈٹ سے رپورٹ بنائیں")}</span>
          </Link>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* FILTER BAR                                                                */}
      {/* ========================================================================= */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-3 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
        {/* Category Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          {(
            [
              { id: "all", en: "All Dossiers", ur: "تمام رپورٹس" },
              { id: "compliance", en: "Building Code", ur: "بلڈنگ کوڈ" },
              { id: "contract", en: "Contract Risk", ur: "معاہدہ خطرات" },
              { id: "cost", en: "Cost & BOQ", ur: "لاگت و تخمینہ" },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleCategoryChange(tab.id)}
              className={cn(
                "px-3 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap",
                activeCategory === tab.id
                  ? "bg-navy-900 dark:bg-white text-white dark:text-navy-900 shadow-2xs"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-navy-800"
              )}
            >
              {language === "ur" ? tab.ur : tab.en}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder={t("Search report title or ID...", "عنوان یا آئی ڈی تلاش کریں...")}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-xs pl-9 pr-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-500/20"
          />
        </div>
      </div>

      {/* ========================================================================= */}
      {/* REPORT CONTENT: EMPTY STATE OR REAL GRID                                  */}
      {/* ========================================================================= */}
      {projects.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 flex items-center justify-center mx-auto">
            <FolderOpen className="w-8 h-8" />
          </div>
          <div className="max-w-md mx-auto space-y-1">
            <h3 className="text-base font-bold text-navy-900 dark:text-white">
              {t("No Construction Projects Found", "کوئی تعمیراتی پروجیکٹ موجود نہیں")}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {t(
                "Create a project workspace in TameerAI to compile engineering compliance dossiers, FIDIC risk assessments, and financial cost intelligence reports.",
                "رپورٹس دیکھنے کے لیے پہلے ایک نیا پروجیکٹ بنائیں اور آڈٹ مکمل کریں۔"
              )}
            </p>
          </div>
          <Link
            href="/dashboard/projects"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 text-white shadow-sm transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>{t("Go to Projects Portfolio", "پروجیکٹس میں جائیں")}</span>
          </Link>
        </div>
      ) : filteredReports.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-slate-100 dark:bg-navy-800 text-slate-400 flex items-center justify-center mx-auto">
            <FileText className="w-8 h-8" />
          </div>
          <div className="max-w-md mx-auto space-y-1">
            <h3 className="text-base font-bold text-navy-900 dark:text-white">
              {t("No formal reports compiled yet for this workspace", "اس ورک اسپیس میں ابھی کوئی رسمی رپورٹ تیار نہیں ہوئی")}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {t(
                "Engineering compliance dossiers, FIDIC risk assessments, and cost intelligence reports are generated when audits or contract analyses are completed.",
                "انجینئرنگ کمپلائنس، فڈک کنٹریکٹ رسک اور لاگت کی رپورٹیں آڈٹ مکمل ہونے پر یہاں خودکار طور پر تیار ہوتی ہیں۔"
              )}
            </p>
          </div>
          <Link
            href="/dashboard/audit"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 text-white shadow-sm transition-all"
          >
            <RefreshCw className="w-4 h-4" />
            <span>{t("Run New Audit to Generate Dossier", "نیا آڈٹ شروع کریں")}</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredReports.map((report) => (
            <div
              key={report.id}
              className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-100 dark:bg-navy-800 text-slate-600 dark:text-slate-300">
                    {report.category}
                  </span>
                  <span className="text-[10px] font-bold text-slate-400 font-mono">
                    {report.id}
                  </span>
                </div>
                <div>
                  <h4 className="text-sm font-bold text-navy-900 dark:text-white line-clamp-2">
                    {language === "ur" && report.titleUrdu ? report.titleUrdu : report.title}
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                    {language === "ur" && report.executiveSummaryUrdu ? report.executiveSummaryUrdu : report.executiveSummary}
                  </p>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100 dark:border-slate-800">
                  <span>{report.pageCount} {t("Pages", "صفحات")}</span>
                  <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">
                    {report.keyMetric || report.status}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 mt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  onClick={() => setPreviewReport(report)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-navy-800"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>{t("Preview", "ملاحظہ")}</span>
                </button>
                {report.storageUrl ? (
                  <a
                    href={report.storageUrl}
                    download
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 text-white"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>{t("Download PDF", "ڈاؤن لوڈ")}</span>
                  </a>
                ) : (
                  <span className="text-[10px] text-slate-400 italic">
                    {t("Archived in DB", "محفوظ شدہ")}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {previewReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-navy-950/60 backdrop-blur-xs p-4">
          <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-orange-500">
                  {previewReport.category} · {previewReport.id}
                </span>
                <h3 className="text-base font-bold text-navy-900 dark:text-white mt-0.5">
                  {previewReport.title}
                </h3>
              </div>
              <button
                onClick={() => setPreviewReport(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-800 space-y-2 text-xs text-slate-700 dark:text-slate-300">
              <p className="font-bold text-slate-900 dark:text-white">{t("Executive Summary:", "خلاصہ:")}</p>
              <p className="leading-relaxed">{previewReport.executiveSummary}</p>
              <div className="pt-2 text-slate-500">
                <p>{t("Author:", "مصنف:")} {previewReport.author}</p>
                <p>{t("Scope:", "دائرہ کار:")} {previewReport.pageCount} {t("Pages", "صفحات")}</p>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setPreviewReport(null)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-navy-800"
              >
                {t("Close", "بند کریں")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
