"use client";

import { useState, useEffect } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  ShieldAlert,
  AlertTriangle,
  FileCheck2,
  HardHat,
  Search,
  CheckCircle2,
  AlertOctagon,
  Info,
  Clock,
  Send,
  Building2,
  ChevronRight,
  Filter,
} from "lucide-react";
import {
  safetyService,
  DamageIndicatorItem,
  SafetyEvaluationResponse,
  PECSignOffResponse,
} from "@/services/safetyService";
import { apiClient } from "@/services/apiClient";

export default function StructuralSafetyPage() {
  const { t, language } = useLanguage();
  const [activeTab, setActiveTab] = useState<"evaluate" | "taxonomy" | "attestation">("evaluate");

  // Triage state
  const [queryText, setQueryText] = useState("");
  const [targetLang, setTargetLang] = useState<"en" | "ur" | "roman_ur">("en");
  const [evaluating, setEvaluating] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState<SafetyEvaluationResponse | null>(null);
  const [evalError, setEvalError] = useState<string | null>(null);

  // Taxonomy catalog state
  const [indicators, setIndicators] = useState<DamageIndicatorItem[]>([]);
  const [loadingIndicators, setLoadingIndicators] = useState(false);
  const [indicatorFilter, setIndicatorFilter] = useState<string>("all");
  const [indicatorSearch, setIndicatorSearch] = useState("");

  // Inspection record / Attestation state
  const [pecNumber, setPecNumber] = useState("");
  const [engineerName, setEngineerName] = useState("");
  const [inspectionDate, setInspectionDate] = useState("");
  const [findingsSummary, setFindingsSummary] = useState("");
  const [attestationStatement, setAttestationStatement] = useState("");
  const [siteInspected, setSiteInspected] = useState(false);
  const [submittingSignOff, setSubmittingSignOff] = useState(false);
  const [signOffResult, setSignOffResult] = useState<PECSignOffResponse | null>(null);
  const [signOffError, setSignOffError] = useState<string | null>(null);

  // Load user name & initial indicators on mount
  useEffect(() => {
    const user = apiClient.getCachedUser();
    if (user?.full_name) {
      setEngineerName(user.full_name);
    }
    if (user?.pec_number) {
      setPecNumber(user.pec_number);
    }

    setLoadingIndicators(true);
    safetyService
      .getIndicators()
      .then((data) => {
        setIndicators(data);
      })
      .finally(() => setLoadingIndicators(false));
  }, []);

  const handleEvaluate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryText.trim()) return;

    setEvaluating(true);
    setEvalError(null);
    try {
      const res = await safetyService.evaluate({
        query: queryText.trim(),
        language: targetLang,
      });
      setEvaluationResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setEvalError(msg || "Evaluation failed. Please verify backend connection.");
    } finally {
      setEvaluating(false);
    }
  };

  const handleSubmitAttestation = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingSignOff(true);
    setSignOffError(null);
    setSignOffResult(null);

    try {
      const res = await safetyService.submitInspectionRecord({
        pec_number: pecNumber.trim(),
        engineer_name: engineerName.trim(),
        physical_site_inspection_conducted: siteInspected,
        inspection_date: inspectionDate ? new Date(inspectionDate).toISOString() : null,
        findings_summary: findingsSummary.trim() || null,
        formal_clearance_issued: false, // Strictly false under Fail-Safe Policy
        attestation_statement: attestationStatement.trim() || null,
      });
      setSignOffResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setSignOffError(msg || "Attestation submission failed.");
    } finally {
      setSubmittingSignOff(false);
    }
  };

  const filteredIndicators = indicators.filter((item) => {
    const matchesCat = indicatorFilter === "all" || item.category === indicatorFilter;
    const matchesSearch =
      indicatorSearch === "" ||
      item.code.toLowerCase().includes(indicatorSearch.toLowerCase()) ||
      item.description.toLowerCase().includes(indicatorSearch.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-orange-50 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-800 rounded-full mb-2">
            <HardHat className="w-3.5 h-3.5 text-orange-600 dark:text-orange-400" />
            <span className="text-[11px] font-bold text-orange-700 dark:text-orange-400 uppercase tracking-wider">
              {t("Structural Safety Advisory Engine (Phase 03.2)", "سٹرکچرل سیفٹی ایڈوائزری انجن")}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white tracking-tight">
            {t("Structural Safety & Hazard Advisory", "سٹرکچرل سیفٹی اور خطرات کی جانچ")}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-2xl">
            {t(
              "Deterministic life-safety triage across 38 Pakistani structural damage indicators. Provides urgent directives and attributable professional inspection logging.",
              "پاکستان کے 38 سٹرکچرل ڈیمیج انڈیکیٹرز پر مبنی مستند جانچ۔ ایمرجنسی احکامات اور فزیکل معائنہ ریکارڈنگ۔"
            )}
          </p>
        </div>

        {/* Tab Navigation Pill */}
        <div className="flex items-center bg-slate-100 dark:bg-navy-900 p-1.5 rounded-xl border border-slate-200 dark:border-slate-800 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab("evaluate")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "evaluate"
                ? "bg-orange-500 text-white shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white"
            }`}
          >
            {t("Hazard Triage", "خطرات کی جانچ")}
          </button>
          <button
            onClick={() => setActiveTab("taxonomy")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "taxonomy"
                ? "bg-orange-500 text-white shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white"
            }`}
          >
            {t("38 Indicators", "38 انڈیکیٹرز")}
          </button>
          <button
            onClick={() => setActiveTab("attestation")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "attestation"
                ? "bg-orange-500 text-white shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white"
            }`}
          >
            {t("Inspection Log", "معائنہ لاگ")}
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: DETERMINISTIC HAZARD EVALUATION & TRIAGE                            */}
      {/* ========================================================================= */}
      {activeTab === "evaluate" && (
        <div className="grid lg:grid-cols-12 gap-6 items-start">
          {/* Query Input Card */}
          <div className="lg:col-span-6 bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
            <h2 className="text-sm font-bold text-navy-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-orange-500" />
              <span>{t("Enter Structural Observation or Query", "سٹرکچرل مسئلہ یا مشاہدہ درج کریں")}</span>
            </h2>

            <form onSubmit={handleEvaluate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1.5">
                  {t("Observation Details (Damage, Cracks, Deflection, Load)", "مشاہدہ کی تفصیل (دراڑیں، جھکاؤ، لوڈ)")}
                </label>
                <textarea
                  rows={4}
                  required
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                  placeholder={
                    language === "ur"
                      ? "مثال: دوسری منزل پر مین کالم کے ساتھ 15 ملی میٹر ترچھی دراڑ نمودار ہوئی ہے اور کنکریٹ جھڑ رہا ہے۔"
                      : "e.g., Deep 15mm diagonal shear crack extending from ground floor beam-column connection with spalling concrete."
                  }
                  className="w-full p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 text-xs sm:text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all placeholder:text-slate-400"
                />
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500">{t("Advisory Language:", "زبان:")}</span>
                  <select
                    value={targetLang}
                    onChange={(e) => setTargetLang(e.target.value as any)}
                    className="text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-navy-950 text-slate-700 dark:text-slate-300"
                  >
                    <option value="en">English (Official)</option>
                    <option value="ur">اردو (Urdu)</option>
                    <option value="roman_ur">Roman Urdu</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={evaluating}
                  className="btn-primary text-xs font-bold px-5 py-2.5 rounded-xl flex items-center gap-2 shadow-sm shadow-orange-500/20"
                >
                  {evaluating ? (
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      <span>{t("Evaluate Severity", "شدت کی جانچ کریں")}</span>
                      <Send className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* Quick Template Examples */}
            <div className="pt-3 border-t border-slate-100 dark:border-slate-800/80">
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                {t("Sample Scenarios for Testing", "آزمائشی مثالیں")}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {[
                  "Column concrete crushing with buckled rebar",
                  "Beam severe diagonal cracking near support",
                  "Slab significant deflection and falling concrete",
                  "Building leaning and multiple damaged elements",
                  "DIY column shoring and jack removal",
                ].map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setQueryText(sample)}
                    className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-orange-50 hover:text-orange-600 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors"
                  >
                    {sample}
                  </button>
                ))}
              </div>
            </div>

            {evalError && (
              <div className="p-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-xs">
                {evalError}
              </div>
            )}
          </div>

          {/* Evaluation Results Card */}
          <div className="lg:col-span-6 bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-xs space-y-5">
            <h2 className="text-sm font-bold text-navy-900 dark:text-white uppercase tracking-wider flex items-center justify-between">
              <span>{t("Deterministic Safety Assessment", "تکنیکی سیفٹی نتیجہ")}</span>
              {evaluationResult && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                  Policy {evaluationResult.policy_version}
                </span>
              )}
            </h2>

            {evaluationResult ? (
              <div className="space-y-4">
                {/* Severity Badge Banner */}
                <div
                  className={`p-4 rounded-xl border flex items-start gap-3.5 ${
                    evaluationResult.severity_code === 0
                      ? "bg-red-50 dark:bg-red-950/50 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200"
                      : evaluationResult.severity_code === 1
                      ? "bg-amber-50 dark:bg-amber-950/50 border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200"
                      : "bg-blue-50 dark:bg-blue-950/50 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-200"
                  }`}
                >
                  <AlertOctagon className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-black uppercase tracking-wider">
                        {evaluationResult.severity_name}
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-white/60 dark:bg-black/40">
                        {evaluationResult.hazard_category.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-xs font-medium mt-1 leading-relaxed">
                      {evaluationResult.rationale}
                    </p>
                  </div>
                </div>

                {/* Evacuation / Inspection Directives */}
                <div className="grid grid-cols-2 gap-3">
                  <div
                    className={`p-3 rounded-xl border text-xs font-semibold ${
                      evaluationResult.requires_immediate_evacuation
                        ? "bg-red-100/70 dark:bg-red-950/40 border-red-300 dark:border-red-800 text-red-700 dark:text-red-300 font-bold"
                        : "bg-slate-50 dark:bg-navy-950 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400"
                    }`}
                  >
                    <p className="text-[10px] uppercase tracking-wider text-slate-500">Evacuation</p>
                    <p className="mt-0.5">
                      {evaluationResult.requires_immediate_evacuation
                        ? "MANDATORY EVACUATION"
                        : "No Evacuation Triggered"}
                    </p>
                  </div>
                  <div
                    className={`p-3 rounded-xl border text-xs font-semibold ${
                      evaluationResult.requires_professional_inspection
                        ? "bg-orange-100/70 dark:bg-orange-950/40 border-orange-300 dark:border-orange-800 text-orange-700 dark:text-orange-300 font-bold"
                        : "bg-slate-50 dark:bg-navy-950 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400"
                    }`}
                  >
                    <p className="text-[10px] uppercase tracking-wider text-slate-500">Engineering Oversight</p>
                    <p className="mt-0.5">
                      {evaluationResult.requires_professional_inspection
                        ? "PEC Engineer Required"
                        : "Standard Monitoring"}
                    </p>
                  </div>
                </div>

                {/* Triggered Damage Indicators */}
                {evaluationResult.damage_indicators.length > 0 && (
                  <div>
                    <h3 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                      {t("Detected Damage Indicators", "شناخت شدہ نقصانات")}
                    </h3>
                    <div className="flex flex-wrap gap-1.5">
                      {evaluationResult.damage_indicators.map((ind, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-1 rounded-md text-xs font-mono font-semibold bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800"
                        >
                          {ind}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Deterministic Safety Advisory */}
                {evaluationResult.safety_advisory && (
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 space-y-2">
                    <h3 className="text-xs font-bold text-orange-600 dark:text-orange-400 uppercase tracking-wider">
                      {t("Safety Directive & Urgent Guidance", "حفاظتی ہدایات و احکامات")}
                    </h3>
                    <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
                      {evaluationResult.safety_advisory}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-12 text-center text-slate-400 dark:text-slate-500">
                <ShieldAlert className="w-10 h-10 mx-auto mb-3 opacity-40" />
                <p className="text-xs font-medium">
                  {t(
                    "Submit an observation on the left to evaluate severity, triggers, and life-safety directives.",
                    "بائیں جانب مشاہدہ درج کریں تاکہ فوری خطرات اور ہدایات کا نتیجہ دیکھا جا سکے۔"
                  )}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: COMPREHENSIVE 38-INDICATOR TAXONOMY CATALOG                         */}
      {/* ========================================================================= */}
      {activeTab === "taxonomy" && (
        <div className="bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-navy-900 dark:text-white">
                {t("Comprehensive 38-Indicator Structural Taxonomy", "38 سٹرکچرل ڈیمیج انڈیکیٹرز کی فہرست")}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {t("Authoritative catalog of structural failure mechanisms and DIY repair hazards.", "تعمیراتی خامیوں اور غیر محفوظ مرمت کے خطرات کی مکمل کیٹلاگ۔")}
              </p>
            </div>

            {/* Search and Category Filters */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder={t("Search indicators...", "تلاش کریں...")}
                  value={indicatorSearch}
                  onChange={(e) => setIndicatorSearch(e.target.value)}
                  className="pl-8 pr-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 text-xs focus:outline-none focus:ring-1 focus:ring-orange-500"
                />
              </div>

              <select
                value={indicatorFilter}
                onChange={(e) => setIndicatorFilter(e.target.value)}
                className="px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 text-xs font-semibold text-slate-700 dark:text-slate-300"
              >
                <option value="all">All Categories ({indicators.length})</option>
                <option value="column">Column (7)</option>
                <option value="beam">Beam (6)</option>
                <option value="slab">Slab (5)</option>
                <option value="building_wide">Building-Wide (6)</option>
                <option value="external_emergency">External Emergency (5)</option>
                <option value="diy_repair_hazard">DIY Repair Hazards (9)</option>
              </select>
            </div>
          </div>

          {/* Indicator Grid */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredIndicators.map((item) => (
              <div
                key={item.code}
                className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-navy-950/40 hover:border-orange-500/40 transition-colors flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                      {item.category.toUpperCase()}
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-navy-900 dark:text-white">
                    {item.description}
                  </h4>
                  <p className="text-[11px] font-mono text-slate-400 mt-1 break-all">
                    {item.code}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: ATTRIBUTABLE PHYSICAL INSPECTION LOG (WITH STATUTORY DISCLAIMER)    */}
      {/* ========================================================================= */}
      {activeTab === "attestation" && (
        <div className="max-w-3xl mx-auto bg-white dark:bg-navy-900 rounded-2xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-xs space-y-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-full mb-2">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
              <span className="text-[11px] font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wider">
                {t("Attributable Observation Record Only", "صرف مشاہداتی معائنہ ریکارڈ")}
              </span>
            </div>
            <h2 className="text-xl font-bold text-navy-900 dark:text-white">
              {t("Professional Engineer Site Inspection Logging", "پیشہ ور انجینئر معائنہ لاگ")}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              {t(
                "Records attributable physical observations and personal professional attestations by verified structural engineers.",
                "مستند انجینئرز کی جانب سے سائیٹ کے ذاتی معائنے کے تکنیکی مشاہدات کا محفوظ اندراج۔"
              )}
            </p>
          </div>

          {/* Mandatory Statutory Notice */}
          <div className="p-4 rounded-xl bg-amber-50/70 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 text-xs text-amber-800 dark:text-amber-300 leading-relaxed">
            <p className="font-bold mb-1">
              {t("Statutory Non-Certification Notice (Phase 03.2.3):", "قانونی نوٹس برائے عدم منظوری:")}
            </p>
            <p>
              {t(
                "TameerAI does NOT issue structural approvals or formal stability clearances. The platform records attributable professional inspection observations and self-attestations only. Formal structural clearance requires an official stamped and sealed PEC engineering report.",
                "TameerAI کوئی رسمی سٹرکچرل منظوری یا سرٹیفیکیشن جاری نہیں کرتا۔ یہ پلیٹ فارم صرف پیشہ ور انجینئر کے معائناتی مشاہدات کا ریکارڈ رکھتا ہے۔ باضابطہ منظوری کے لیے پی ای سی کی مہر شدہ رپورٹ لازمی ہے۔"
              )}
            </p>
          </div>

          {/* Attestation Form */}
          <form onSubmit={handleSubmitAttestation} className="space-y-4">
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  {t("PEC Registration Number", "پی ای سی رجسٹریشن نمبر")}
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CIVIL/44910 or STRUCT/12034"
                  value={pecNumber}
                  onChange={(e) => setPecNumber(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 text-xs sm:text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-orange-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  {t("Engineer Full Legal Name", "انجینئر کا مکمل نام")}
                </label>
                <input
                  type="text"
                  required
                  placeholder="Engr. Muhammad Ali"
                  value={engineerName}
                  onChange={(e) => setEngineerName(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 text-xs sm:text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-orange-500"
                />
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  {t("Physical Inspection Date", "سائیٹ معائنہ کی تاریخ")}
                </label>
                <input
                  type="date"
                  value={inspectionDate}
                  onChange={(e) => setInspectionDate(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 text-xs sm:text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-orange-500"
                />
              </div>

              <div className="flex items-center pt-6">
                <input
                  id="site-inspected-check"
                  type="checkbox"
                  checked={siteInspected}
                  onChange={(e) => setSiteInspected(e.target.checked)}
                  className="w-4 h-4 rounded text-orange-500 focus:ring-orange-400 border-slate-300 dark:border-slate-700 bg-white dark:bg-navy-900 cursor-pointer"
                />
                <label
                  htmlFor="site-inspected-check"
                  className="ml-2.5 text-xs font-semibold text-slate-700 dark:text-slate-300 cursor-pointer"
                >
                  {t(
                    "I personally conducted an on-site physical inspection.",
                    "میں نے ذاتی طور پر سائیٹ کا فزیکل معائنہ کیا ہے۔"
                  )}
                </label>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                {t("Technical Findings Summary", "تکنیکی مشاہدات کی سمری")}
              </label>
              <textarea
                rows={3}
                value={findingsSummary}
                onChange={(e) => setFindingsSummary(e.target.value)}
                placeholder={t(
                  "Summarize visual inspection, core testing, crack monitors, or rebar exposure...",
                  "دراڑوں کے مانیٹر، کنکریٹ کی حالت، اور سٹرکچرل صورتحال کا خلاصہ..."
                )}
                className="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 text-xs sm:text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-orange-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                {t("Professional Attestation Statement", "پیشہ ورانہ بیان")}
              </label>
              <textarea
                rows={2}
                value={attestationStatement}
                onChange={(e) => setAttestationStatement(e.target.value)}
                placeholder={t(
                  "I hereby attest that I inspected the described structural members and recorded true observations.",
                  "میں تصدیق کرتا ہوں کہ میں نے بیان کردہ سٹرکچرل حصوں کا معائنہ کیا ہے اور درست مشاہدات درج کیے ہیں۔"
                )}
                className="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 text-xs sm:text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-orange-500"
              />
            </div>

            <button
              type="submit"
              disabled={submittingSignOff}
              className="w-full py-3 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-orange-500 hover:bg-orange-600 shadow-md shadow-orange-500/20 transition-all flex items-center justify-center gap-2"
            >
              {submittingSignOff ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>{t("Submit Attributable Inspection Record", "مشاہداتی ریکارڈ جمع کریں")}</span>
                  <FileCheck2 className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {signOffError && (
            <div className="p-3.5 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-xs">
              {signOffError}
            </div>
          )}

          {signOffResult && (
            <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-200 space-y-2">
              <div className="flex items-center gap-2 font-bold">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Inspection Record Attributed & Fingerprinted</span>
              </div>
              <p>Record ID: <span className="font-mono">{signOffResult.sign_off_id}</span></p>
              <p>Status: <span className="font-bold">{signOffResult.clearance_status}</span></p>
              {signOffResult.provenance_hash && (
                <p className="break-all font-mono text-[10px] text-slate-500">
                  Fingerprint SHA-256: {signOffResult.provenance_hash}
                </p>
              )}
              <p className="text-[11px] text-slate-600 dark:text-slate-400 border-t border-emerald-200 dark:border-emerald-800/60 pt-2">
                {signOffResult.regulatory_notice}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

