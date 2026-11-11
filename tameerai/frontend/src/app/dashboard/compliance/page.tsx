"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Info,
  Layers,
  FileText,
  RefreshCw,
  Building2,
  ChevronRight,
  ArrowRight,
  PlusCircle,
  FolderOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { projectService } from "@/services/projectService";
import { apiClient } from "@/services/apiClient";
import { Project } from "@/types";

export interface ComplianceAuditItem {
  id: string;
  project_id: string;
  code?: string;
  status: string;
  scope_description?: string;
  bylaw_set: string;
  created_at: string;
  findings_count?: number;
}

export default function CompliancePage() {
  const { t } = useLanguage();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [audits, setAudits] = useState<ComplianceAuditItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadInitialData() {
      setLoading(true);
      try {
        const projs = await projectService.getProjects();
        setProjects(projs);
        if (projs.length > 0) {
          setSelectedProjectId(projs[0].id);
          await loadAuditsForProject(projs[0].id);
        }
      } catch (err) {
        console.error("[CompliancePage] Initial fetch error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadInitialData();
  }, []);

  const loadAuditsForProject = async (projectId: string) => {
    try {
      const resp = await apiClient.get<ComplianceAuditItem[]>(
        `/projects/${projectId}/compliance-audits`
      );
      setAudits(Array.isArray(resp) ? resp : []);
    } catch {
      setAudits([]);
    }
  };

  const handleSelectProject = async (projectId: string) => {
    setSelectedProjectId(projectId);
    setLoading(true);
    await loadAuditsForProject(projectId);
    setLoading(false);
  };

  const currentProject = projects.find((p) => p.id === selectedProjectId) || null;

  return (
    <div className="space-y-6 pb-12 font-sans max-w-7xl mx-auto">
      {/* 1. TOP HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20">
              {t("Statutory Bylaws Enforcement", "بلڈنگ بائی لاز تعمیل")}
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {t("Building Code of Pakistan (PBC 2021) Engine", "پی بی سی 2021 معیار")}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white tracking-tight flex items-center gap-2.5">
            <ShieldCheck className="w-6 h-6 text-orange-500" />
            <span>{t("Compliance Verification", "تعمیل کی جانچ (Compliance Check)")}</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {t(
              "Deterministic checking of dimensional setbacks, fire exit corridors, Means of Egress, and structural parameters against PBC 2021 and municipal authority bylaws.",
              "عمارت کے نقشہ جات کی پی بی سی 2021 اور مجاز اتھارٹیز کے قوانین کے تحت مستند جانچ۔"
            )}
          </p>
        </div>

        {/* Project Selector */}
        {projects.length > 0 && (
          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4 text-orange-500" />
            <select
              value={selectedProjectId}
              onChange={(e) => handleSelectProject(e.target.value)}
              className="px-3 py-1.5 rounded-xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 text-xs font-bold text-navy-900 dark:text-white focus:outline-none cursor-pointer"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.id})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* 2. STATS ROW */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {t("Governing Standard", "بنیادی معیار")}
          </p>
          <p className="text-base sm:text-lg font-black text-navy-900 dark:text-white mt-1">
            PBC 2021
          </p>
          <span className="text-[10px] text-slate-400">
            {t("Pakistan Building Code", "پاکستان بلڈنگ کوڈ")}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {t("Target Jurisdiction", "علاقائی دائرہ اختیار")}
          </p>
          <p className="text-base sm:text-lg font-black text-navy-900 dark:text-white mt-1">
            {currentProject ? currentProject.city : "National"}
          </p>
          <span className="text-[10px] text-slate-400">
            {currentProject ? currentProject.governingAuthority || "LDA / SBCA / CDA" : "LDA / SBCA / CDA"}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {t("Active Audits", "فعال آڈٹ")}
          </p>
          <p className="text-base sm:text-lg font-black text-amber-600 dark:text-amber-400 mt-1">
            {audits.length}
          </p>
          <span className="text-[10px] text-slate-400">
            {t("Workspace Records", "ریکارڈز")}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {t("Engine Mode", "انجن موڈ")}
          </p>
          <p className="text-base sm:text-lg font-black text-emerald-600 dark:text-emerald-400 mt-1">
            Deterministic
          </p>
          <span className="text-[10px] text-slate-400">
            {t("No Hallucinated Findings", "حقیقی قواعد")}
          </span>
        </div>
      </div>

      {/* 3. AUDITS LIST OR INFORMATIVE EMPTY STATE */}
      {loading ? (
        <div className="p-12 bg-white dark:bg-navy-900 rounded-3xl border border-slate-200 dark:border-slate-800 text-center animate-pulse">
          <div className="h-6 bg-slate-200 dark:bg-slate-800 rounded w-48 mx-auto mb-3" />
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-72 mx-auto" />
        </div>
      ) : audits.length === 0 ? (
        <div className="bg-white dark:bg-navy-900 rounded-3xl p-10 sm:p-14 border border-slate-200/90 dark:border-slate-800 text-center max-w-2xl mx-auto shadow-sm">
          <div className="w-16 h-16 rounded-2xl bg-orange-500/10 text-orange-500 border border-orange-500/20 flex items-center justify-center mx-auto mb-4">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h2 className="text-lg font-bold text-navy-900 dark:text-white mb-2">
            {t(
              "No Active Compliance Audits for this Workspace",
              "اس ورک اسپیس کے لیے کوئی آڈٹ ریکارڈ نہیں ملا"
            )}
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-6 max-w-md mx-auto">
            {t(
              "To audit setbacks, FAR, height zoning, and egress corridors against PBC 2021 bylaws, upload your architectural drawing and initiate an audit in the Audit Center.",
              "پی بی سی 2021 کے تحت سیٹ بیک اور بلڈنگ ہائٹ کی جانچ کے لیے نیا آڈٹ شروع کریں۔"
            )}
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href="/dashboard/audit"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs uppercase tracking-wider shadow-md shadow-orange-500/20 transition-all"
            >
              <PlusCircle className="w-4 h-4" />
              <span>{t("Start New Compliance Audit", "نیا تعمیل آڈٹ شروع کریں")}</span>
            </Link>

            {currentProject && (
              <Link
                href={`/dashboard/projects/${currentProject.id}`}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-bold text-xs uppercase tracking-wider transition-colors"
              >
                <span>{t("Upload Blueprint to Workspace", "ورک اسپیس میں نقشہ اپ لوڈ کریں")}</span>
              </Link>
            )}
          </div>

          <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-400">
            {t(
              "PBC 2021 vector parsing operates deterministically on verified project blueprints. No simulated violations are generated.",
              "پی بی سی 2021 کی جانچ تصدیق شدہ نقشہ جات پر حقیقی طور پر لاگو کی جاتی ہے۔ کوئی فرضی رپورٹس جاری نہیں کی جاتیں۔"
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <h2 className="text-sm font-bold text-navy-900 dark:text-white uppercase tracking-wider">
            {t("Project Audit Dossiers", "پروجیکٹ آڈٹ فائلیں")}
          </h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {audits.map((a) => (
              <div
                key={a.id}
                className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 shadow-2xs flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs font-bold text-slate-500">
                      {a.code || a.id}
                    </span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950 text-amber-700">
                      {a.status}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-navy-900 dark:text-white mb-1">
                    {a.bylaw_set}
                  </h3>
                  <p className="text-xs text-slate-500 mb-4">
                    {a.scope_description || "Comprehensive building code inspection"}
                  </p>
                </div>
                <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-400">
                  <span>{new Date(a.created_at).toLocaleDateString()}</span>
                  <span className="text-orange-500 font-bold">{a.findings_count || 0} findings</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
