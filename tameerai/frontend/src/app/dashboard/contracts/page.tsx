"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  FileText,
  UploadCloud,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Scale,
  Sparkles,
  Download,
  RefreshCw,
  Search,
  Filter,
  ExternalLink,
  Bot,
  Clock,
  Coins,
  ShieldAlert,
  ChevronRight,
  BookOpen,
  ArrowRight,
  Check,
  X,
  FileCheck,
  FolderOpen,
  PlusCircle,
  Building2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { projectService } from "@/services/projectService";
import { contractService, ContractAnalysis } from "@/services/contractService";
import { Project, ContractRiskCard } from "@/types";

export default function ContractAnalyzerPage() {
  const { t, language } = useLanguage();

  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [analyses, setAnalyses] = useState<ContractAnalysis[]>([]);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string>("");
  const [riskCards, setRiskCards] = useState<ContractRiskCard[]>([]);
  const [selectedRiskId, setSelectedRiskId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [loadingCards, setLoadingCards] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newFormat, setNewFormat] = useState("FIDIC Red Book (1999/2017)");

  const loadCards = useCallback(async (projId: string, analysisId: string) => {
    setLoadingCards(true);
    try {
      const cards = await contractService.getRiskCards(projId, analysisId);
      setRiskCards(cards);
      if (cards.length > 0) {
        setSelectedRiskId(cards[0].id);
      } else {
        setSelectedRiskId("");
      }
    } catch (err) {
      console.error("[ContractPage] Error loading risk cards:", err);
      setRiskCards([]);
    } finally {
      setLoadingCards(false);
    }
  }, []);

  const loadAnalyses = useCallback(async (projId: string) => {
    if (!projId) {
      setAnalyses([]);
      setRiskCards([]);
      return;
    }
    setLoading(true);
    try {
      const data = await contractService.getProjectAnalyses(projId);
      setAnalyses(data);
      if (data.length > 0) {
        setSelectedAnalysisId(data[0].id);
        await loadCards(projId, data[0].id);
      } else {
        setSelectedAnalysisId("");
        setRiskCards([]);
      }
    } catch (err) {
      console.error("[ContractPage] Error loading analyses:", err);
      setAnalyses([]);
      setRiskCards([]);
    } finally {
      setLoading(false);
    }
  }, [loadCards]);

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
          await loadAnalyses(firstId);
        }
      } catch (err) {
        console.error("[ContractPage] Error loading projects:", err);
      } finally {
        setLoading(false);
      }
    }
    loadProjects();
  }, [loadAnalyses]);

  const handleProjectChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const projId = e.target.value;
    setSelectedProjectId(projId);
    await loadAnalyses(projId);
  };

  const handleAnalysisChange = async (analysisId: string) => {
    setSelectedAnalysisId(analysisId);
    if (selectedProjectId) {
      await loadCards(selectedProjectId, analysisId);
    }
  };

  const handleCreateAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId || !newTitle.trim()) return;

    try {
      setLoading(true);
      const created = await contractService.createAnalysis(selectedProjectId, {
        contractTitle: newTitle.trim(),
        standardFormat: newFormat,
      });
      setIsCreating(false);
      setNewTitle("");
      if (created) {
        await loadAnalyses(selectedProjectId);
      }
    } catch (err) {
      console.error("[ContractPage] Failed to create analysis:", err);
      alert("Failed to initialize contract analysis dossier.");
    } finally {
      setLoading(false);
    }
  };

  const activeAnalysis = analyses.find((a) => a.id === selectedAnalysisId) || analyses[0];
  const activeRisk = riskCards.find((r) => r.id === selectedRiskId) || riskCards[0];

  return (
    <div className="space-y-6 pb-12 font-sans">
      {/* ========================================================================= */}
      {/* PAGE HEADER                                                               */}
      {/* ========================================================================= */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
              {t("FIDIC & PEC Risk Intelligence", "فڈک اور پی ای سی رسک انٹیلی جنس")}
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {t("Grounded in Official Standards", "سرکاری معیارات کے مطابق")}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white tracking-tight flex items-center gap-2.5">
            <Scale className="w-6 h-6 text-orange-500" />
            <span>{t("Contract Analyzer", "معاہدہ تجزیہ کار (Contract Analyzer)")}</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {t(
              "Audits construction contracts and subcontractor agreements against FIDIC Red/Yellow Books and PEC standard bidding guidelines.",
              "تعمیراتی معاہدات اور سب کانٹریکٹ شرائط کا فڈک اور پی ای سی قواعد کے تحت تفصیلی تجزیہ۔"
            )}
          </p>
        </div>

        {/* Workspace Project Selector */}
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

          <button
            onClick={() => setIsCreating(true)}
            disabled={!selectedProjectId}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white shadow-sm transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>{t("New Contract Analysis", "نیا معاہدہ تجزیہ")}</span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* CREATE ANALYSIS MODAL                                                     */}
      {/* ========================================================================= */}
      {isCreating && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-navy-950/60 backdrop-blur-xs p-4">
          <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-navy-900 dark:text-white flex items-center gap-2">
                <Scale className="w-5 h-5 text-orange-500" />
                <span>{t("Initialize Contract Analysis", "نیا کنٹریکٹ تجزیہ شروع کریں")}</span>
              </h3>
              <button
                onClick={() => setIsCreating(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateAnalysis} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  {t("Contract Document Title", "معاہدے کا عنوان")}
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Subcontract Agreement - Structural Works"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  {t("Standard Contract Baseline", "معیاری فریم ورک")}
                </label>
                <select
                  value={newFormat}
                  onChange={(e) => setNewFormat(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20"
                >
                  <option value="FIDIC Red Book (1999/2017)">FIDIC Red Book (1999/2017)</option>
                  <option value="FIDIC Yellow Book (Plant & Design-Build)">FIDIC Yellow Book</option>
                  <option value="PEC Standard Bidding Procedure">PEC Standard Bidding Procedure</option>
                  <option value="Private Subcontract Agreement">Private Subcontract Agreement</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreating(false)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-navy-800"
                >
                  {t("Cancel", "منسوخ")}
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 text-white"
                >
                  {loading ? t("Creating...", "تخلیق جاری...") : t("Create Analysis Dossier", "تجزیہ ڈوزیئر بنائیں")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* EMPTY STATE: NO PROJECTS OR NO ANALYSES                                    */}
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
                "Create a project workspace in TameerAI to upload construction contracts, evaluate FIDIC liability terms, and track legal exposure.",
                "معاہدہ تجزیہ کار استعمال کرنے کے لیے پہلے ایک نیا پروجیکٹ بنائیں اور معاہداتی دستاویزات منسلک کریں۔"
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
      ) : analyses.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 flex items-center justify-center mx-auto">
            <Scale className="w-8 h-8" />
          </div>
          <div className="max-w-md mx-auto space-y-1">
            <h3 className="text-base font-bold text-navy-900 dark:text-white">
              {t("No Contract Risk Analyses in this Workspace", "اس پروجیکٹ میں ابھی کوئی معاہداتی تجزیہ نہیں ہوا")}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {t(
                "Upload a contract agreement or initialize a new analysis dossier to audit liquidated damages, retention ceilings, and payment period clauses against FIDIC / PEC standards.",
                "معاہدے کا آڈٹ شروع کرنے کے لیے نیا تجزیہ ڈوزیئر شامل کریں یا آڈٹ انجن استعمال کریں۔"
              )}
            </p>
          </div>
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={() => setIsCreating(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 text-white shadow-sm transition-all"
            >
              <PlusCircle className="w-4 h-4" />
              <span>{t("Initialize Analysis Dossier", "تجزیہ ڈوزیئر شروع کریں")}</span>
            </button>
            <Link
              href="/dashboard/audit"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 dark:hover:bg-navy-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition-all"
            >
              <RefreshCw className="w-4 h-4" />
              <span>{t("Run Audit Wizard", "آڈٹ وزرڈ میں جائیں")}</span>
            </Link>
          </div>
        </div>
      ) : (
        <>
          {/* Active Analysis Banner */}
          <div className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3.5 min-w-0">
              <div className="w-12 h-12 rounded-2xl bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 flex items-center justify-center flex-shrink-0">
                <FileText className="w-6 h-6" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold text-navy-900 dark:text-white truncate">
                    {activeAnalysis.contractTitle}
                  </h2>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-black uppercase bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                    {activeAnalysis.status}
                  </span>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  {activeAnalysis.standardFormat} · {t("Audited clauses:", "جانچ شدہ شقیں:")} {activeAnalysis.totalClausesAudited} · {t("Flagged:", "نشاندہی:")} {activeAnalysis.flaggedClausesCount}
                </p>
              </div>
            </div>

            {/* Analysis Switcher if multiple exist */}
            {analyses.length > 1 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">{t("Switch Analysis:", "تجزیہ منتخب کریں:")}</span>
                <select
                  value={selectedAnalysisId}
                  onChange={(e) => handleAnalysisChange(e.target.value)}
                  className="bg-slate-100 dark:bg-navy-800 text-xs font-bold text-slate-800 dark:text-slate-200 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700"
                >
                  {analyses.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.contractTitle} ({a.id})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Metrics Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                {t("Risk Score", "خطرہ اسکور")}
              </span>
              <div className="text-3xl font-black text-rose-600 dark:text-rose-400 font-mono mt-1">
                {activeAnalysis.riskScore !== undefined ? `${activeAnalysis.riskScore}/10` : "N/A"}
              </div>
              <p className="text-xs text-slate-500 mt-1">
                {activeAnalysis.riskCategory || t("Risk level assessed", "خطرہ کی سطح")}
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                {t("Total Clauses Audited", "کل جانچ شدہ شقیں")}
              </span>
              <div className="text-3xl font-black text-navy-900 dark:text-white font-mono mt-1">
                {activeAnalysis.totalClausesAudited}
              </div>
              <p className="text-xs text-slate-500 mt-1">{t("Scanned against standard", "معیار کے مطابق جائزہ")}</p>
            </div>

            <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                {t("Flagged Risk Clauses", "نشاندہی شدہ شقیں")}
              </span>
              <div className="text-3xl font-black text-amber-500 font-mono mt-1">
                {activeAnalysis.flaggedClausesCount}
              </div>
              <p className="text-xs text-slate-500 mt-1">{t("Requires contractor amendment", "ترمیم درکار ہے")}</p>
            </div>

            <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                {t("Compliance Standard", "معیار")}
              </span>
              <div className="text-sm font-bold text-navy-900 dark:text-white mt-1 line-clamp-1">
                {activeAnalysis.standardFormat}
              </div>
              <p className="text-xs text-slate-500 mt-1">{t("FIDIC & PEC Guidelines", "فڈک اور پی ای سی قواعد")}</p>
            </div>
          </div>

          {/* Risk Cards List & Detail View */}
          {riskCards.length === 0 ? (
            <div className="p-8 text-center rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {t(
                  "No specific clause risk cards flagged for this contract dossier yet.",
                  "اس معاہداتی تجزیے کے تحت ابھی کوئی شق فلیگ نہیں ہوئی۔"
                )}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Risk Cards List */}
              <div className="lg:col-span-5 space-y-3">
                <h3 className="text-xs font-black uppercase tracking-wider text-slate-400">
                  {t("Flagged Risk Clauses", "نشاندہی شدہ شقیں")} ({riskCards.length})
                </h3>
                {riskCards.map((card) => {
                  const isSelected = card.id === selectedRiskId;
                  return (
                    <div
                      key={card.id}
                      onClick={() => setSelectedRiskId(card.id)}
                      className={cn(
                        "p-4 rounded-xl border cursor-pointer transition-all space-y-2",
                        isSelected
                          ? "bg-orange-50/50 dark:bg-orange-950/20 border-orange-500 shadow-xs"
                          : "bg-white dark:bg-navy-900 border-slate-200/80 dark:border-slate-800 hover:border-slate-300"
                      )}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-bold text-navy-900 dark:text-white line-clamp-1">
                          {language === "ur" && card.clauseTitleUrdu ? card.clauseTitleUrdu : card.clauseTitle}
                        </span>
                        <span
                          className={cn(
                            "px-2 py-0.5 rounded text-[10px] font-bold uppercase",
                            card.riskLevel === "high"
                              ? "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400"
                              : card.riskLevel === "medium"
                              ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                              : "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                          )}
                        >
                          {card.riskLevel}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                        {card.fidicReference} {card.pageNumber ? `· Page ${card.pageNumber}` : ""}
                      </p>
                      <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-2">
                        {language === "ur" && card.explanationUrdu ? card.explanationUrdu : card.explanation}
                      </p>
                    </div>
                  );
                })}
              </div>

              {/* Right Column: Detailed View */}
              <div className="lg:col-span-7">
                {activeRisk && (
                  <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-5">
                    <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
                      <div>
                        <h4 className="text-base font-bold text-navy-900 dark:text-white">
                          {language === "ur" && activeRisk.clauseTitleUrdu
                            ? activeRisk.clauseTitleUrdu
                            : activeRisk.clauseTitle}
                        </h4>
                        <p className="text-xs text-slate-500 font-mono mt-0.5">
                          {activeRisk.fidicReference}
                        </p>
                      </div>
                      <span
                        className={cn(
                          "px-2.5 py-1 rounded-lg text-xs font-bold uppercase",
                          activeRisk.riskLevel === "high"
                            ? "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-400"
                            : "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400"
                        )}
                      >
                        {activeRisk.riskLevelLabel}
                      </span>
                    </div>

                    <div className="space-y-2">
                      <span className="text-xs font-black uppercase tracking-wider text-slate-400">
                        {t("Raw Clause Snippet", "معاہدے کا اصل متن")}
                      </span>
                      <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 font-mono text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                        {activeRisk.rawClauseSnippet}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <span className="text-xs font-black uppercase tracking-wider text-slate-400">
                        {t("Risk Assessment & Legal Impact", "قانونی و مالی خطرہ")}
                      </span>
                      <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                        {language === "ur" && activeRisk.explanationUrdu
                          ? activeRisk.explanationUrdu
                          : activeRisk.explanation}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/40 space-y-1.5">
                      <span className="text-xs font-bold text-emerald-800 dark:text-emerald-400 flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>{t("Recommended Contractor Amendment", "مجوزہ ترمیم")}</span>
                      </span>
                      <p className="text-xs text-emerald-900 dark:text-emerald-300 leading-relaxed">
                        {language === "ur" && activeRisk.recommendationUrdu
                          ? activeRisk.recommendationUrdu
                          : activeRisk.recommendation}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
