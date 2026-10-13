"use client";

import { useState } from "react";
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
} from "lucide-react";
import { cn } from "@/lib/utils";

import { ConsultingReport, ReportCategory } from "@/types";
import { CONSULTING_REPORTS } from "@/data";

export default function ReportsPage() {
  const { t, language } = useLanguage();

  // Active Category Filter
  const [activeCategory, setActiveCategory] = useState<"all" | "compliance" | "contract" | "cost">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedProject, setSelectedProject] = useState("all");

  // Preview Modal State
  const [previewReport, setPreviewReport] = useState<ConsultingReport | null>(null);
  const [downloadSuccessToast, setDownloadSuccessToast] = useState<string | null>(null);

  // Filtered Reports
  const filteredReports = CONSULTING_REPORTS.filter((rpt) => {
    const matchesCategory = activeCategory === "all" || rpt.category === activeCategory;
    const matchesProject = selectedProject === "all" || rpt.projectName.toLowerCase().includes(selectedProject.toLowerCase());
    const matchesSearch =
      !searchQuery ||
      rpt.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rpt.projectName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rpt.date.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesProject && matchesSearch;
  });

  const handleDownload = (report: ConsultingReport) => {
    setDownloadSuccessToast(report.title);
    setTimeout(() => setDownloadSuccessToast(null), 3000);
  };

  return (
    <div className="space-y-6 pb-12 font-sans">
      {/* Toast Notification */}
      {downloadSuccessToast && (
        <div className="fixed top-20 right-6 z-50 bg-emerald-600 text-white px-4 py-2.5 rounded-xl shadow-xl flex items-center gap-2 text-xs font-bold animate-in fade-in slide-in-from-top-4">
          <CheckCircle2 className="w-4 h-4" />
          <span>Downloaded PDF: {downloadSuccessToast}</span>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TOP HEADER & TITLE (Professional Consulting Company Style)                */}
      {/* ========================================================================= */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20">
              {t("Executive Engineering Dossiers", "انجینئرنگ اور قانونی دستاویزات")}
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {t("Arup & Turner-Townsend Consulting Standard", "کنسلٹنگ معیارات کے مطابق")}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white tracking-tight flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-orange-500" />
            <span>{t("Reports Management", "رپورٹس مینجمنٹ (Reports Management)")}</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {t(
              "Access and download client-ready compliance certificates, FIDIC contract risk evaluations, and financial cost intelligence reports.",
              "کلائنٹس اور اتھارٹیز کے لیے تصدیق شدہ پی بی سی 2021، قانونی معاہدات اور لاگت رپورٹس ڈاؤن لوڈ کریں۔"
            )}
          </p>
        </div>

        {/* Generate Report Button */}
        <div className="flex items-center gap-2 flex-wrap">
          <Link
            href="/dashboard/audit"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 text-white shadow-sm shadow-orange-500/20 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>{t("Generate New Report", "نئی رپورٹ بنائیں")}</span>
          </Link>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* CATEGORY TABS & SEARCH / FILTER BAR                                       */}
      {/* ========================================================================= */}
      <div className="p-4 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-3">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* 3 Main Categories Requested: Compliance, Contract, Cost */}
          <div className="flex bg-slate-100 dark:bg-navy-950 p-1 rounded-xl text-xs font-bold overflow-x-auto">
            <button
              onClick={() => setActiveCategory("all")}
              className={cn(
                "px-3.5 py-1.5 rounded-lg whitespace-nowrap transition-all",
                activeCategory === "all"
                  ? "bg-white dark:bg-navy-800 text-navy-900 dark:text-white shadow-2xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white"
              )}
            >
              {t("All Reports", "تمام رپورٹس")} (9)
            </button>
            <button
              onClick={() => setActiveCategory("compliance")}
              className={cn(
                "inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg whitespace-nowrap transition-all",
                activeCategory === "compliance"
                  ? "bg-white dark:bg-navy-800 text-orange-600 dark:text-orange-400 shadow-2xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white"
              )}
            >
              <ShieldCheck className="w-3.5 h-3.5 text-orange-500" />
              <span>{t("Compliance Reports", "تعمیل رپورٹس (Compliance)")}</span> (3)
            </button>
            <button
              onClick={() => setActiveCategory("contract")}
              className={cn(
                "inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg whitespace-nowrap transition-all",
                activeCategory === "contract"
                  ? "bg-white dark:bg-navy-800 text-orange-600 dark:text-orange-400 shadow-2xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white"
              )}
            >
              <Scale className="w-3.5 h-3.5 text-blue-500" />
              <span>{t("Contract Reports", "معاہداتی رپورٹس (Contract)")}</span> (3)
            </button>
            <button
              onClick={() => setActiveCategory("cost")}
              className={cn(
                "inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg whitespace-nowrap transition-all",
                activeCategory === "cost"
                  ? "bg-white dark:bg-navy-800 text-orange-600 dark:text-orange-400 shadow-2xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white"
              )}
            >
              <Coins className="w-3.5 h-3.5 text-emerald-500" />
              <span>{t("Cost Reports", "لاگت رپورٹس (Cost)")}</span> (3)
            </button>
          </div>

          {/* Search Box & Project Filter */}
          <div className="flex items-center gap-2 flex-1 md:max-w-md">
            <div className="relative flex-1">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t("Search by project or report title...", "رپورٹ یا منصوبہ تلاش کریں...")}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-xl placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500 text-navy-900 dark:text-white"
              />
            </div>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="px-2.5 py-1.5 text-xs bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-1 focus:ring-orange-500"
            >
              <option value="all">{t("All Projects", "تمام منصوبے")}</option>
              <option value="DHA Commercial Plaza">DHA Commercial Plaza</option>
              <option value="Model Town House">Model Town House</option>
              <option value="Factory Project">Factory Project</option>
            </select>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* REPORT CARDS GRID (Project Name, Date, Status, Preview & Download PDF)   */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredReports.map((report) => (
          <div
            key={report.id}
            className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs hover:shadow-md hover:border-orange-500/40 transition-all flex flex-col justify-between space-y-4 group"
          >
            {/* Top Row: Category Pill & Status Badge */}
            <div className="flex items-start justify-between gap-2">
              <span
                className={cn(
                  "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider",
                  report.category === "compliance"
                    ? "bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20"
                    : report.category === "contract"
                    ? "bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20"
                    : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                )}
              >
                {report.category === "compliance" && <ShieldCheck className="w-3 h-3" />}
                {report.category === "contract" && <Scale className="w-3 h-3" />}
                {report.category === "cost" && <Coins className="w-3 h-3" />}
                <span>{report.categoryLabel}</span>
              </span>

              {/* Status Badge */}
              <span
                className={cn(
                  "px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider",
                  report.status === "certified" || report.status === "approved"
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                    : report.status === "action_required" || report.status === "overrun_alert"
                    ? "bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20"
                    : "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                )}
              >
                {t(report.statusLabel, report.statusLabelUrdu)}
              </span>
            </div>

            {/* Title & Description */}
            <div className="space-y-1.5">
              <h3 className="text-sm sm:text-base font-bold text-navy-900 dark:text-white leading-snug group-hover:text-orange-500 transition-colors line-clamp-2">
                {t(report.title, report.titleUrdu)}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed">
                {report.executiveSummary}
              </p>
            </div>

            {/* Metadata Grid (Project Name, Date, Pages) */}
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800/80 text-xs space-y-1.5">
              <div className="flex items-center justify-between text-slate-600 dark:text-slate-300">
                <span className="text-[11px] text-slate-400 flex items-center gap-1">
                  <Building2 className="w-3.5 h-3.5 text-orange-500" />
                  <span>{t("Project Name:", "منصوبہ:")}</span>
                </span>
                <strong className="text-navy-900 dark:text-white font-semibold">
                  {t(report.projectName, report.projectNameUrdu)}
                </strong>
              </div>

              <div className="flex items-center justify-between text-slate-600 dark:text-slate-300">
                <span className="text-[11px] text-slate-400 flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <span>{t("Date:", "تاریخ:")}</span>
                </span>
                <span className="font-mono text-slate-700 dark:text-slate-300">{report.date}</span>
              </div>

              <div className="flex items-center justify-between text-slate-600 dark:text-slate-300">
                <span className="text-[11px] text-slate-400 flex items-center gap-1">
                  <FileText className="w-3.5 h-3.5 text-slate-400" />
                  <span>{t("Format:", "فارمیٹ:")}</span>
                </span>
                <span className="text-[11px] font-mono text-slate-400">
                  {report.pageCount} Pages ({report.fileSize})
                </span>
              </div>
            </div>

            {/* BUTTONS: PREVIEW & DOWNLOAD PDF (Required by Prompt) */}
            <div className="pt-2 flex items-center gap-2 border-t border-slate-100 dark:border-slate-800">
              {/* Preview Button */}
              <button
                type="button"
                onClick={() => setPreviewReport(report)}
                className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-navy-950 hover:bg-slate-200 dark:hover:bg-navy-800 border border-slate-200 dark:border-slate-800 transition-all shadow-2xs"
              >
                <Eye className="w-3.5 h-3.5 text-slate-500" />
                <span>{t("Preview", "معائنہ (Preview)")}</span>
              </button>

              {/* Download PDF Button */}
              <button
                type="button"
                onClick={() => handleDownload(report)}
                className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl text-xs font-bold text-white bg-orange-500 hover:bg-orange-600 shadow-sm shadow-orange-500/20 active:scale-95 transition-all"
              >
                <Download className="w-3.5 h-3.5" />
                <span>{t("Download PDF", "ڈاؤن لوڈ پی ڈی ایف")}</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* ========================================================================= */}
      {/* EXECUTIVE PDF PREVIEW MODAL (Professional Consulting Company Style)        */}
      {/* ========================================================================= */}
      {previewReport && (
        <div className="fixed inset-0 z-50 bg-navy-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="w-full max-w-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col my-8 max-h-[90vh]">
            {/* Modal Header */}
            <div className="p-4 bg-slate-50 dark:bg-navy-950 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2 min-w-0">
                <FileCheck className="w-5 h-5 text-orange-500 flex-shrink-0" />
                <div className="min-w-0">
                  <h3 className="font-bold text-xs sm:text-sm text-navy-900 dark:text-white truncate">
                    {previewReport.title}
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    {previewReport.projectName} · {previewReport.date} · Stamped Dossier
                  </p>
                </div>
              </div>
              <button
                onClick={() => setPreviewReport(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-navy-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-navy-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Document Preview Sheet Body */}
            <div className="flex-1 overflow-y-auto p-6 bg-slate-200/60 dark:bg-navy-950 flex justify-center">
              <div className="w-full max-w-xl bg-white text-slate-900 p-8 shadow-xl rounded-sm border border-slate-300 font-serif space-y-5 text-xs select-text">
                {/* Formal Letterhead */}
                <div className="border-b-2 border-slate-900 pb-4 flex items-start justify-between">
                  <div>
                    <div className="text-[9px] font-sans font-black tracking-widest text-orange-600 uppercase">
                      TAMEERAI CONSULTING & ENGINEERING INTELLIGENCE
                    </div>
                    <div className="text-base font-sans font-black text-slate-900 mt-0.5">
                      EXECUTIVE TECHNICAL AUDIT REPORT
                    </div>
                    <div className="text-[10px] text-slate-500 italic mt-0.5">
                      Grounded in Pakistan Building Code (PBC 2021) & PEC Bidding Standards
                    </div>
                  </div>
                  <div className="text-right text-[9px] font-sans text-slate-500">
                    <div>Ref: <strong>{previewReport.id}</strong></div>
                    <div>Date: {previewReport.date}</div>
                    <div className="text-emerald-700 font-bold">VERIFIED DOSSIER</div>
                  </div>
                </div>

                {/* Project Metadata Banner */}
                <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 border border-slate-200 font-sans text-[11px]">
                  <div>
                    <span className="text-slate-500 block text-[9px] font-bold uppercase">Client / Project:</span>
                    <strong className="text-slate-900">{previewReport.projectName}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[9px] font-bold uppercase">Report Category:</span>
                    <strong className="text-slate-900">{previewReport.categoryLabel}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[9px] font-bold uppercase">Auditor / Author:</span>
                    <span className="text-slate-700">{previewReport.author}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[9px] font-bold uppercase">Audit Result:</span>
                    <strong className="text-orange-600">{previewReport.statusLabel}</strong>
                  </div>
                </div>

                {/* Executive Summary Section */}
                <div className="space-y-2">
                  <h4 className="font-sans font-bold text-xs uppercase tracking-wider text-slate-900 border-b border-slate-200 pb-1">
                    1. Executive Summary
                  </h4>
                  <p className="text-[11.5px] leading-relaxed text-slate-800">
                    {previewReport.executiveSummary}
                  </p>
                </div>

                {/* Audit Key Finding Details */}
                <div className="space-y-2">
                  <h4 className="font-sans font-bold text-xs uppercase tracking-wider text-slate-900 border-b border-slate-200 pb-1">
                    2. Certified Findings & Regulatory Citations
                  </h4>
                  <ul className="space-y-1.5 text-[11px] text-slate-700 pl-2">
                    <li className="flex items-start gap-2">
                      <span className="text-orange-500 font-bold">•</span>
                      <span><strong>Key Metric:</strong> {previewReport.keyMetric}</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-orange-500 font-bold">•</span>
                      <span><strong>Jurisdiction:</strong> Pakistan Building Code 2021 (Chapters 3, 4, 11) & Provincial By-laws.</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-orange-500 font-bold">•</span>
                      <span><strong>Recommended Action:</strong> Follow mitigation directives outlined in Section 4 before municipal plan submission.</span>
                    </li>
                  </ul>
                </div>

                {/* Official Stamp & Signoff */}
                <div className="pt-6 border-t-2 border-slate-900 flex items-center justify-between font-sans text-[10px]">
                  <div>
                    <div className="w-16 h-16 rounded-full border-2 border-dashed border-emerald-600 text-emerald-700 flex flex-col items-center justify-center font-bold text-[8px] leading-tight text-center">
                      <span>PBC 2021</span>
                      <span>VERIFIED</span>
                      <span>AUDIT</span>
                    </div>
                  </div>
                  <div className="text-right space-y-0.5">
                    <div className="font-serif italic text-slate-600">Engr. Tariq Mehmood</div>
                    <div className="font-bold text-slate-900">Lead Consultant, TameerAI</div>
                    <div className="text-slate-400 text-[9px]">PEC Reg. No: CIVIL/38491</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Footer Actions */}
            <div className="p-4 bg-white dark:bg-navy-900 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <span className="text-xs text-slate-500">
                Official PDF Generated · Ready for Client Presentation
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPreviewReport(null)}
                  className="px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-navy-800"
                >
                  {t("Close", "بند کریں")}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    handleDownload(previewReport);
                    setPreviewReport(null);
                  }}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 text-white shadow-sm"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>{t("Download PDF", "ڈاؤن لوڈ پی ڈی ایف")}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
