"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  Building2,
  MapPin,
  Coins,
  UploadCloud,
  FileSpreadsheet,
  FileText,
  Image as ImageIcon,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  ShieldCheck,
  Calculator,
  Scale,
  Cpu,
  FileCheck,
  AlertTriangle,
  X,
  FileCode,
  Layers,
  HelpCircle,
  Play,
  RotateCcw,
} from "lucide-react";
import { cn } from "@/lib/utils";

// Building Type Options
const BUILDING_TYPES = [
  { id: "commercial", en: "Commercial Plaza / Mall", ur: "کمرشل پلازہ / شاپنگ مال", icon: Building2 },
  { id: "residential", en: "Residential (House / Apts)", ur: "رہائشی (مکان / اپارٹمنٹس)", icon: Building2 },
  { id: "mixed_use", en: "Mixed-Use Development", ur: "مخلوط استعمال کی عمارت", icon: Layers },
  { id: "industrial", en: "Industrial / Factory", ur: "صنعتی / فیکٹری", icon: Building2 },
];

// Major Pakistani Cities
const PAKISTAN_CITIES = [
  { name: "Lahore", nameUrdu: "لاہور", authority: "LDA / DHA Lahore" },
  { name: "Karachi", nameUrdu: "کراچی", authority: "SBCA / DHA Karachi" },
  { name: "Islamabad", nameUrdu: "اسلام آباد", authority: "CDA / Rawalpindi RDA" },
  { name: "Rawalpindi", nameUrdu: "راولپنڈی", authority: "RDA / Cantt Board" },
  { name: "Faisalabad", nameUrdu: "فیصل آباد", authority: "FDA" },
  { name: "Multan", nameUrdu: "ملتان", authority: "MDA / DHA Multan" },
  { name: "Peshawar", nameUrdu: "پشاور", authority: "PDA / DHA Peshawar" },
];

export default function NewAuditPage() {
  const { t, language } = useLanguage();
  const router = useRouter();

  // Wizard Step (1, 2, 3)
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);

  // Step 1: Project Information
  const [projectName, setProjectName] = useState("DHA Commercial Plaza");
  const [buildingType, setBuildingType] = useState("commercial");
  const [locationCity, setLocationCity] = useState("Lahore");
  const [locationArea, setLocationArea] = useState("DHA Phase 6, Main Boulevard");
  const [budgetCrores, setBudgetCrores] = useState("12");
  const [totalCoveredArea, setTotalCoveredArea] = useState("45,000");
  const [floorsCount, setFloorsCount] = useState("6");

  // Step 2: Upload Files State
  const [buildingPlanFile, setBuildingPlanFile] = useState<string | null>("DHA_Commercial_Plaza_Arch_Rev3.pdf");
  const [boqFile, setBoqFile] = useState<string | null>("DHA_Plaza_Itemized_BOQ_Schedule.xlsx");
  const [contractFile, setContractFile] = useState<string | null>("FIDIC_Subcontractor_Agreement_2024.pdf");
  const [siteImages, setSiteImages] = useState<string[]>([
    "Foundation_Rebar_Inspection_Site1.jpg",
    "Excavation_Soil_Bed_View.png",
  ]);

  // Step 3: Choose Analysis Type
  const [selectedAnalysis, setSelectedAnalysis] = useState<"compliance" | "contract" | "cost" | "full">("full");

  // Execution Modal / Running Animation State
  const [isAuditing, setIsAuditing] = useState(false);
  const [auditProgress, setAuditProgress] = useState(0);
  const [auditCurrentTask, setAuditCurrentTask] = useState("");
  const [auditComplete, setAuditComplete] = useState(false);

  // Pre-fill Sample Helper
  const handleLoadSampleData = () => {
    setProjectName("DHA Commercial Plaza");
    setBuildingType("commercial");
    setLocationCity("Lahore");
    setLocationArea("DHA Phase 6, Sector CCA");
    setBudgetCrores("12");
    setTotalCoveredArea("48,000");
    setFloorsCount("G + 5 Floors");
    setBuildingPlanFile("DHA_Plaza_Architectural_Floorplans_v4.dwg.pdf");
    setBoqFile("DHA_Plaza_Structural_Steel_Cement_BOQ.xlsx");
    setContractFile("FIDIC_Standard_Subcontract_Agreement.pdf");
    setSiteImages(["Site_Foundation_Rebar_Inspection.jpg", "Column_Shuttering_Check.jpg"]);
    setSelectedAnalysis("full");
  };

  // Launch Audit Simulation
  const handleStartAudit = () => {
    setIsAuditing(true);
    setAuditProgress(10);
    setAuditCurrentTask(t("Parsing CAD drawings & calculating clear widths...", "نقشے کا معائنہ اور چوڑائی کا حساب جاری..."));

    setTimeout(() => {
      setAuditProgress(40);
      setAuditCurrentTask(t("Auditing compliance against Pakistan Building Code (PBC 2021)...", "پی بی سی 2021 کے تحت تعمیل کی جانچ..."));
    }, 1200);

    setTimeout(() => {
      setAuditProgress(70);
      setAuditCurrentTask(t("Cross-referencing BOQ items with Lahore Steel Gr.60 index...", "سٹیل اور سیمنٹ کے مارکیٹ ریٹس کی تصدیق..."));
    }, 2400);

    setTimeout(() => {
      setAuditProgress(90);
      setAuditCurrentTask(t("Scanning contract liquidated damages & penalty clauses...", "معاہدے کے ممکنہ قانونی خطرات کا تجزیہ..."));
    }, 3600);

    setTimeout(() => {
      setAuditProgress(100);
      setAuditCurrentTask(t("Audit Complete! Generating intelligence dashboard...", "آڈٹ مکمل! انٹیلی جنس ڈیش بورڈ تیار ہے..."));
      setAuditComplete(true);
    }, 4800);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12 font-sans">
      {/* ========================================================================= */}
      {/* PAGE HEADER                                                               */}
      {/* ========================================================================= */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20">
              {t("TameerAI Neural Engine", "تعمیر اے آئی نیورل انجن")}
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {t("Grounded in PBC 2021 & FIDIC", "پی بی سی 2021 اور فڈک پر مبنی")}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white tracking-tight">
            {t("Start New Construction Audit", "نیا تعمیراتی آڈٹ شروع کریں")}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t(
              "Configure project parameters, upload blueprints & contracts, and run automated AI intelligence.",
              "منصوبے کی تفصیلات درج کریں، نقشہ جات و معاہدے اپ لوڈ کریں اور خودکار اے آئی تجزیہ شروع کریں۔"
            )}
          </p>
        </div>

        {/* Load Sample Demo Button */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleLoadSampleData}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-orange-600 dark:text-orange-400 bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/20 transition-all shadow-2xs"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{t("Load DHA Plaza Sample", "ڈی ایچ اے پلازہ ڈیٹا لوڈ کریں")}</span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* STEP-BY-STEP WIZARD PROGRESS BAR                                          */}
      {/* ========================================================================= */}
      <div className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
        <div className="grid grid-cols-3 gap-2 sm:gap-4 relative">
          {/* Step 1 Pill */}
          <button
            onClick={() => setCurrentStep(1)}
            className={cn(
              "flex flex-col sm:flex-row items-center sm:items-start gap-2.5 p-2 sm:p-3 rounded-xl transition-all text-left",
              currentStep === 1
                ? "bg-orange-50 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-800 shadow-2xs"
                : currentStep > 1
                ? "bg-slate-50 dark:bg-navy-950/40 text-slate-700 dark:text-slate-300"
                : "text-slate-400 dark:text-slate-500 opacity-70"
            )}
          >
            <div
              className={cn(
                "w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0 transition-colors shadow-2xs",
                currentStep === 1
                  ? "bg-orange-500 text-white"
                  : currentStep > 1
                  ? "bg-emerald-500 text-white"
                  : "bg-slate-200 dark:bg-slate-800 text-slate-500"
              )}
            >
              {currentStep > 1 ? <CheckCircle2 className="w-4 h-4" /> : "1"}
            </div>
            <div className="min-w-0 text-center sm:text-left">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                {t("Step 1", "مرحلہ 1")}
              </span>
              <p
                className={cn(
                  "text-xs sm:text-sm font-bold truncate",
                  currentStep === 1 ? "text-orange-600 dark:text-orange-400" : "text-navy-900 dark:text-white"
                )}
              >
                {t("Project Information", "منصوبے کی معلومات")}
              </p>
            </div>
          </button>

          {/* Step 2 Pill */}
          <button
            onClick={() => setCurrentStep(2)}
            className={cn(
              "flex flex-col sm:flex-row items-center sm:items-start gap-2.5 p-2 sm:p-3 rounded-xl transition-all text-left",
              currentStep === 2
                ? "bg-orange-50 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-800 shadow-2xs"
                : currentStep > 2
                ? "bg-slate-50 dark:bg-navy-950/40 text-slate-700 dark:text-slate-300"
                : "text-slate-400 dark:text-slate-500 opacity-70"
            )}
          >
            <div
              className={cn(
                "w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0 transition-colors shadow-2xs",
                currentStep === 2
                  ? "bg-orange-500 text-white"
                  : currentStep > 2
                  ? "bg-emerald-500 text-white"
                  : "bg-slate-200 dark:bg-slate-800 text-slate-500"
              )}
            >
              {currentStep > 2 ? <CheckCircle2 className="w-4 h-4" /> : "2"}
            </div>
            <div className="min-w-0 text-center sm:text-left">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                {t("Step 2", "مرحلہ 2")}
              </span>
              <p
                className={cn(
                  "text-xs sm:text-sm font-bold truncate",
                  currentStep === 2 ? "text-orange-600 dark:text-orange-400" : "text-navy-900 dark:text-white"
                )}
              >
                {t("Upload Documents", "دستاویزات اپ لوڈ")}
              </p>
            </div>
          </button>

          {/* Step 3 Pill */}
          <button
            onClick={() => setCurrentStep(3)}
            className={cn(
              "flex flex-col sm:flex-row items-center sm:items-start gap-2.5 p-2 sm:p-3 rounded-xl transition-all text-left",
              currentStep === 3
                ? "bg-orange-50 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-800 shadow-2xs"
                : "text-slate-400 dark:text-slate-500 opacity-70"
            )}
          >
            <div
              className={cn(
                "w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0 transition-colors shadow-2xs",
                currentStep === 3
                  ? "bg-orange-500 text-white"
                  : "bg-slate-200 dark:bg-slate-800 text-slate-500"
              )}
            >
              3
            </div>
            <div className="min-w-0 text-center sm:text-left">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                {t("Step 3", "مرحلہ 3")}
              </span>
              <p
                className={cn(
                  "text-xs sm:text-sm font-bold truncate",
                  currentStep === 3 ? "text-orange-600 dark:text-orange-400" : "text-navy-900 dark:text-white"
                )}
              >
                {t("Choose Analysis", "تجزیہ منتخب کریں")}
              </p>
            </div>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* STEP 1: PROJECT INFORMATION                                               */}
      {/* ========================================================================= */}
      {currentStep === 1 && (
        <div className="p-5 sm:p-7 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-6">
          <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
            <h2 className="text-base sm:text-lg font-bold text-navy-900 dark:text-white flex items-center gap-2">
              <Building2 className="w-5 h-5 text-orange-500" />
              <span>{t("Project Information", "منصوبے کی بنیادی معلومات")}</span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {t(
                "Specify the project name, classification, location jurisdiction, and total allocated budget.",
                "منصوبے کا نام، عمارت کی قسم، متعلقہ اتھارٹی اور کل بجٹ درج کریں۔"
              )}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Project Name */}
            <div className="space-y-1.5 md:col-span-2">
              <label className="text-xs font-bold text-navy-900 dark:text-slate-200 flex items-center justify-between">
                <span>{t("Project Name", "منصوبے کا نام")} *</span>
                <span className="text-[11px] font-normal text-slate-400">
                  {t("e.g. DHA Commercial Plaza, Model Town House", "مثال: ڈی ایچ اے کمرشل پلازہ")}
                </span>
              </label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="Enter project name..."
                className="w-full px-3.5 py-2.5 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-navy-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all"
              />
            </div>

            {/* Building Type */}
            <div className="space-y-1.5 md:col-span-2">
              <label className="text-xs font-bold text-navy-900 dark:text-slate-200">
                {t("Building Type", "عمارت کی قسم")} *
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {BUILDING_TYPES.map((bt) => {
                  const Icon = bt.icon;
                  const isSelected = buildingType === bt.id;
                  return (
                    <button
                      key={bt.id}
                      type="button"
                      onClick={() => setBuildingType(bt.id)}
                      className={cn(
                        "p-3 rounded-xl border text-left transition-all flex flex-col justify-between gap-2",
                        isSelected
                          ? "bg-orange-50 dark:bg-orange-950/40 border-orange-500 text-orange-600 dark:text-orange-400 ring-2 ring-orange-500/20 shadow-2xs"
                          : "bg-slate-50 dark:bg-navy-950 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-700"
                      )}
                    >
                      <Icon className={cn("w-5 h-5", isSelected ? "text-orange-500" : "text-slate-400")} />
                      <span className="text-xs font-bold leading-tight">{t(bt.en, bt.ur)}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Location (City & Authority) */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-navy-900 dark:text-slate-200 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-orange-500" />
                <span>{t("City & Authority", "شہر اور اتھارٹی")} *</span>
              </label>
              <select
                value={locationCity}
                onChange={(e) => setLocationCity(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all"
              >
                {PAKISTAN_CITIES.map((c) => (
                  <option key={c.name} value={c.name}>
                    {t(c.name, c.nameUrdu)} ({c.authority})
                  </option>
                ))}
              </select>
            </div>

            {/* Location Specific Area */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-navy-900 dark:text-slate-200">
                {t("Area / Sector Details", "علاقہ / سیکٹر کی تفصیل")} *
              </label>
              <input
                type="text"
                value={locationArea}
                onChange={(e) => setLocationArea(e.target.value)}
                placeholder="e.g. DHA Phase 6, Main Boulevard"
                className="w-full px-3.5 py-2.5 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-navy-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all"
              />
            </div>

            {/* Budget */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-navy-900 dark:text-slate-200 flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <Coins className="w-3.5 h-3.5 text-emerald-500" />
                  <span>{t("Budget (Crores PKR)", "کل بجٹ (کروڑ روپے)")} *</span>
                </span>
                <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-bold">
                  ≈ PKR {(parseFloat(budgetCrores || "0") * 10000000).toLocaleString()}
                </span>
              </label>
              <div className="relative">
                <input
                  type="number"
                  step="0.5"
                  value={budgetCrores}
                  onChange={(e) => setBudgetCrores(e.target.value)}
                  placeholder="12"
                  className="w-full px-3.5 py-2.5 pr-20 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 font-bold transition-all"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
                  {t("Crore", "کروڑ")}
                </span>
              </div>
              {/* Quick Budget selector chips */}
              <div className="flex gap-1.5 pt-1">
                {["2", "5", "12", "25", "50"].map((v) => (
                  <button
                    key={v}
                    type="button"
                    onClick={() => setBudgetCrores(v)}
                    className={cn(
                      "px-2 py-0.5 rounded-md text-[10px] font-bold border transition-colors",
                      budgetCrores === v
                        ? "bg-orange-500 text-white border-orange-500"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:border-orange-500"
                    )}
                  >
                    {v} {t("Cr", "کروڑ")}
                  </button>
                ))}
              </div>
            </div>

            {/* Covered Area & Floors */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-navy-900 dark:text-slate-200">
                  {t("Covered Area (sq ft)", "رقبہ (مربع فٹ)")}
                </label>
                <input
                  type="text"
                  value={totalCoveredArea}
                  onChange={(e) => setTotalCoveredArea(e.target.value)}
                  placeholder="45,000"
                  className="w-full px-3 py-2.5 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-navy-900 dark:text-slate-200">
                  {t("Number of Floors", "منزلوں کی تعداد")}
                </label>
                <input
                  type="text"
                  value={floorsCount}
                  onChange={(e) => setFloorsCount(e.target.value)}
                  placeholder="G + 5"
                  className="w-full px-3 py-2.5 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
                />
              </div>
            </div>
          </div>

          {/* Step 1 Actions */}
          <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-end">
            <button
              type="button"
              onClick={() => setCurrentStep(2)}
              disabled={!projectName.trim()}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 disabled:bg-slate-300 dark:disabled:bg-slate-800 text-white font-bold text-xs sm:text-sm shadow-md shadow-orange-500/20 transition-all"
            >
              <span>{t("Next: Upload Documents", "اگلا مرحلہ: دستاویزات اپ لوڈ")}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 2: UPLOAD (Building Plan, BOQ Excel, Contract PDF, Images)            */}
      {/* ========================================================================= */}
      {currentStep === 2 && (
        <div className="p-5 sm:p-7 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-6">
          <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
            <h2 className="text-base sm:text-lg font-bold text-navy-900 dark:text-white flex items-center gap-2">
              <UploadCloud className="w-5 h-5 text-orange-500" />
              <span>{t("Upload Project Documents & Drawings", "منصوبے کی فائلیں اور ڈرائنگز اپ لوڈ کریں")}</span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {t(
                "Upload your architectural CAD/PDF plans, BOQ cost Excel sheets, legal contracts, and site inspection pictures.",
                "آرکیٹیکچرل نقشے، بی او کیو شیٹس، معاہدات اور سائٹ کی تصاویر اپ لوڈ کریں۔"
              )}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 1. Building Plan */}
            <div className="p-4 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50/60 dark:bg-navy-950/60 flex flex-col justify-between space-y-3 hover:border-orange-500/60 transition-all">
              <div className="flex items-start justify-between gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 flex items-center justify-center flex-shrink-0">
                  <FileCode className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-xs sm:text-sm font-bold text-navy-900 dark:text-white truncate">
                      {t("Building Plan", "عمارت کا نقشہ (Building Plan)")}
                    </h3>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400">
                      PDF / DWG
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {t("Floorplans, elevations, staircase & column drawings", "فلور پلانز، ایلیویشن، سیڑھی اور کالم کے نقشے")}
                  </p>
                </div>
              </div>

              {buildingPlanFile ? (
                <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between text-xs text-emerald-800 dark:text-emerald-300 font-medium">
                  <div className="flex items-center gap-2 truncate">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                    <span className="truncate">{buildingPlanFile}</span>
                  </div>
                  <button
                    onClick={() => setBuildingPlanFile(null)}
                    className="p-1 hover:text-rose-500 transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <label className="cursor-pointer block text-center py-4 px-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-900 hover:bg-orange-50/50 transition-colors">
                  <UploadCloud className="w-5 h-5 mx-auto text-slate-400 mb-1" />
                  <span className="text-xs font-semibold text-orange-500 block">
                    {t("Click to upload Building Plan", "نقشہ اپ لوڈ کرنے کے لیے کلک کریں")}
                  </span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">
                    Max size: 50MB (.dwg, .dxf, .pdf)
                  </span>
                  <input
                    type="file"
                    className="hidden"
                    onChange={(e) => setBuildingPlanFile(e.target.files?.[0]?.name || "Architectural_Plan.pdf")}
                  />
                </label>
              )}
            </div>

            {/* 2. BOQ Excel */}
            <div className="p-4 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50/60 dark:bg-navy-950/60 flex flex-col justify-between space-y-3 hover:border-orange-500/60 transition-all">
              <div className="flex items-start justify-between gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 flex items-center justify-center flex-shrink-0">
                  <FileSpreadsheet className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-xs sm:text-sm font-bold text-navy-900 dark:text-white truncate">
                      {t("BOQ Excel", "بی او کیو شیٹ (BOQ Excel)")}
                    </h3>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                      XLSX / CSV
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {t("Bill of Quantities with steel, cement, rebar quantities", "اسٹیل، سیمنٹ اور میٹریل کی شیٹ")}
                  </p>
                </div>
              </div>

              {boqFile ? (
                <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between text-xs text-emerald-800 dark:text-emerald-300 font-medium">
                  <div className="flex items-center gap-2 truncate">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                    <span className="truncate">{boqFile}</span>
                  </div>
                  <button
                    onClick={() => setBoqFile(null)}
                    className="p-1 hover:text-rose-500 transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <label className="cursor-pointer block text-center py-4 px-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-900 hover:bg-emerald-50/50 transition-colors">
                  <UploadCloud className="w-5 h-5 mx-auto text-slate-400 mb-1" />
                  <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 block">
                    {t("Click to upload BOQ Excel", "بی او کیو ایکسل اپ لوڈ کریں")}
                  </span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">
                    Max size: 25MB (.xlsx, .xls, .csv)
                  </span>
                  <input
                    type="file"
                    className="hidden"
                    onChange={(e) => setBoqFile(e.target.files?.[0]?.name || "BOQ_Schedule.xlsx")}
                  />
                </label>
              )}
            </div>

            {/* 3. Contract PDF */}
            <div className="p-4 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50/60 dark:bg-navy-950/60 flex flex-col justify-between space-y-3 hover:border-orange-500/60 transition-all">
              <div className="flex items-start justify-between gap-3">
                <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 flex items-center justify-center flex-shrink-0">
                  <FileText className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-xs sm:text-sm font-bold text-navy-900 dark:text-white truncate">
                      {t("Contract PDF", "معاہدہ دستاویز (Contract PDF)")}
                    </h3>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-purple-500/10 text-purple-600 dark:text-purple-400">
                      PDF / DOCX
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {t("Subcontract agreement, FIDIC terms, penalty clauses", "سب کنٹریکٹ اور فڈک شرائط")}
                  </p>
                </div>
              </div>

              {contractFile ? (
                <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between text-xs text-emerald-800 dark:text-emerald-300 font-medium">
                  <div className="flex items-center gap-2 truncate">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                    <span className="truncate">{contractFile}</span>
                  </div>
                  <button
                    onClick={() => setContractFile(null)}
                    className="p-1 hover:text-rose-500 transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <label className="cursor-pointer block text-center py-4 px-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-900 hover:bg-purple-50/50 transition-colors">
                  <UploadCloud className="w-5 h-5 mx-auto text-slate-400 mb-1" />
                  <span className="text-xs font-semibold text-purple-600 dark:text-purple-400 block">
                    {t("Click to upload Contract PDF", "معاہدہ دستاویز اپ لوڈ کریں")}
                  </span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">
                    Max size: 30MB (.pdf, .docx)
                  </span>
                  <input
                    type="file"
                    className="hidden"
                    onChange={(e) => setContractFile(e.target.files?.[0]?.name || "Contract_Agreement.pdf")}
                  />
                </label>
              )}
            </div>

            {/* 4. Images */}
            <div className="p-4 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50/60 dark:bg-navy-950/60 flex flex-col justify-between space-y-3 hover:border-orange-500/60 transition-all">
              <div className="flex items-start justify-between gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 flex items-center justify-center flex-shrink-0">
                  <ImageIcon className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-xs sm:text-sm font-bold text-navy-900 dark:text-white truncate">
                      {t("Site Images", "سائٹ کی تصاویر (Site Images)")}
                    </h3>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400">
                      JPG / PNG
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {t("Excavation, rebar binds, foundation, shuttering photos", "بنیاد اور کنکریٹ شٹرنگ کی تصاویر")}
                  </p>
                </div>
              </div>

              {siteImages.length > 0 ? (
                <div className="space-y-1.5">
                  {siteImages.map((img, i) => (
                    <div
                      key={i}
                      className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between text-xs text-emerald-800 dark:text-emerald-300 font-medium"
                    >
                      <div className="flex items-center gap-2 truncate">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                        <span className="truncate">{img}</span>
                      </div>
                      <button
                        onClick={() => setSiteImages(siteImages.filter((_, idx) => idx !== i))}
                        className="p-0.5 hover:text-rose-500 transition-colors"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <label className="cursor-pointer block text-center py-4 px-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-900 hover:bg-amber-50/50 transition-colors">
                  <UploadCloud className="w-5 h-5 mx-auto text-slate-400 mb-1" />
                  <span className="text-xs font-semibold text-amber-600 dark:text-amber-400 block">
                    {t("Click to upload Site Photos", "سائٹ کی تصاویر اپ لوڈ کریں")}
                  </span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">
                    Upload multiple (.jpg, .png)
                  </span>
                  <input
                    type="file"
                    multiple
                    className="hidden"
                    onChange={(e) => {
                      const files = Array.from(e.target.files || []).map((f) => f.name);
                      setSiteImages((prev) => [...prev, ...files]);
                    }}
                  />
                </label>
              )}
            </div>
          </div>

          {/* Step 2 Actions */}
          <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setCurrentStep(1)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all border border-slate-200 dark:border-slate-700"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>{t("Back: Project Info", "پچھلا مرحلہ: معلومات")}</span>
            </button>
            <button
              type="button"
              onClick={() => setCurrentStep(3)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs sm:text-sm shadow-md shadow-orange-500/20 transition-all"
            >
              <span>{t("Next: Choose Analysis", "اگلا مرحلہ: تجزیہ کا انتخاب")}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 3: CHOOSE ANALYSIS & START AUDIT BUTTON                              */}
      {/* ========================================================================= */}
      {currentStep === 3 && (
        <div className="p-5 sm:p-7 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-6">
          <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
            <h2 className="text-base sm:text-lg font-bold text-navy-900 dark:text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-orange-500" />
              <span>{t("Choose Analysis Mode", "تجزیہ کا موڈ منتخب کریں")}</span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {t(
                "Select whether you want a specific single-module scan or the full comprehensive 360° AI Construction Audit.",
                "کوئی مخصوص اسکین منتخب کریں یا مکمل جامع 360 ڈگری اے آئی آڈٹ چلائیں۔"
              )}
            </p>
          </div>

          {/* 4 Analysis Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* 1. Compliance Check */}
            <div
              onClick={() => setSelectedAnalysis("compliance")}
              className={cn(
                "cursor-pointer p-4 rounded-2xl border transition-all relative flex flex-col justify-between",
                selectedAnalysis === "compliance"
                  ? "bg-orange-50 dark:bg-orange-950/40 border-orange-500 ring-2 ring-orange-500/20 shadow-sm"
                  : "bg-slate-50 dark:bg-navy-950 border-slate-200 dark:border-slate-800 hover:border-slate-300"
              )}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 flex items-center justify-center">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-bold text-slate-400">~45 sec</span>
                </div>
                <h3 className="text-sm font-bold text-navy-900 dark:text-white">
                  {t("Compliance Check", "بلڈنگ کوڈ تعمیل کی جانچ (Compliance Check)")}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                  {t(
                    "Audits staircase widths, column spacing, seismic zone factor, and LDA/CDA zoning setbacks against PBC 2021.",
                    "پاکستان بلڈنگ کوڈ 2021 کے تحت سیڑھی کی چوڑائی، کالم اور زلزلہ زون کی تصدیق۔"
                  )}
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-200/60 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
                <span>PBC 2021 Chapter 4 & 5</span>
                <span className="font-bold text-orange-500">{selectedAnalysis === "compliance" ? "Selected" : "Select"}</span>
              </div>
            </div>

            {/* 2. Contract Analysis */}
            <div
              onClick={() => setSelectedAnalysis("contract")}
              className={cn(
                "cursor-pointer p-4 rounded-2xl border transition-all relative flex flex-col justify-between",
                selectedAnalysis === "contract"
                  ? "bg-orange-50 dark:bg-orange-950/40 border-orange-500 ring-2 ring-orange-500/20 shadow-sm"
                  : "bg-slate-50 dark:bg-navy-950 border-slate-200 dark:border-slate-800 hover:border-slate-300"
              )}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 flex items-center justify-center">
                    <Scale className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-bold text-slate-400">~35 sec</span>
                </div>
                <h3 className="text-sm font-bold text-navy-900 dark:text-white">
                  {t("Contract Analysis", "معاہدہ کا قانونی تجزیہ (Contract Analysis)")}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                  {t(
                    "Identifies unlimited liquidated damages, unfair penalty clauses, and missing price escalation protections in FIDIC agreements.",
                    "فڈک معاہدات میں غیر منصفانہ جرمانے اور قیمتوں میں اضافے کے خطرات کی نشاندہی۔"
                  )}
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-200/60 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
                <span>FIDIC 2017 & PEC Standards</span>
                <span className="font-bold text-orange-500">{selectedAnalysis === "contract" ? "Selected" : "Select"}</span>
              </div>
            </div>

            {/* 3. Cost Analysis */}
            <div
              onClick={() => setSelectedAnalysis("cost")}
              className={cn(
                "cursor-pointer p-4 rounded-2xl border transition-all relative flex flex-col justify-between",
                selectedAnalysis === "cost"
                  ? "bg-orange-50 dark:bg-orange-950/40 border-orange-500 ring-2 ring-orange-500/20 shadow-sm"
                  : "bg-slate-50 dark:bg-navy-950 border-slate-200 dark:border-slate-800 hover:border-slate-300"
              )}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 flex items-center justify-center">
                    <Calculator className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-bold text-slate-400">~40 sec</span>
                </div>
                <h3 className="text-sm font-bold text-navy-900 dark:text-white">
                  {t("Cost Analysis", "لاگت و تخمینہ کا تجزیہ (Cost Analysis)")}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                  {t(
                    "Benchmarks BOQ line items against live steel (Gr.60), cement, and brick rates in Lahore/Karachi/Islamabad.",
                    "موجودہ مارکیٹ ریٹس کے مطابق مٹیریل کی قیمتوں اور اووررن کا تخمینہ۔"
                  )}
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-200/60 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
                <span>Verified Pakistan Index</span>
                <span className="font-bold text-orange-500">{selectedAnalysis === "cost" ? "Selected" : "Select"}</span>
              </div>
            </div>

            {/* 4. Full Audit (Recommended) */}
            <div
              onClick={() => setSelectedAnalysis("full")}
              className={cn(
                "cursor-pointer p-4 rounded-2xl border-2 transition-all relative flex flex-col justify-between",
                selectedAnalysis === "full"
                  ? "bg-gradient-to-br from-orange-500/10 via-amber-500/5 to-transparent border-orange-500 ring-2 ring-orange-500/30 shadow-md"
                  : "bg-slate-50 dark:bg-navy-950 border-slate-300 dark:border-slate-700 hover:border-orange-500/50"
              )}
            >
              <div className="absolute top-3 right-3">
                <span className="px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider bg-orange-500 text-white shadow-2xs">
                  {t("Recommended", "تجویز کردہ")}
                </span>
              </div>

              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 text-white flex items-center justify-center shadow-xs">
                    <Sparkles className="w-5 h-5" />
                  </div>
                </div>
                <h3 className="text-sm font-black text-navy-900 dark:text-white">
                  {t("Full Audit", "مکمل جامع آڈٹ (Full Audit 360°)")}
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 leading-relaxed font-medium">
                  {t(
                    "All-in-one comprehensive analysis: PBC 2021 compliance check, FIDIC contract risk review, and real-time BOQ cost variance intelligence.",
                    "مکمل ہمہ جہتی تجزیہ: بلڈنگ کوڈ، معاہداتی خطرات اور لائیو لاگت کی مکمل رپورٹ۔"
                  )}
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-orange-500/20 flex items-center justify-between text-[11px] text-orange-600 dark:text-orange-400 font-bold">
                <span>Compliance + Contract + Cost</span>
                <span>{selectedAnalysis === "full" ? "✓ Selected" : "Select"}</span>
              </div>
            </div>
          </div>

          {/* Audit Configuration Summary Box */}
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-xs space-y-2">
            <h4 className="font-bold text-navy-900 dark:text-white uppercase tracking-wider text-[11px]">
              {t("Audit Configuration Summary", "آڈٹ کنفیگریشن خلاصہ")}
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-slate-600 dark:text-slate-400">
              <div>
                <span className="text-[10px] text-slate-400 block">{t("Project:", "منصوبہ:")}</span>
                <strong className="text-navy-900 dark:text-white">{projectName}</strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">{t("Jurisdiction:", "علاقہ:")}</span>
                <strong className="text-navy-900 dark:text-white">{locationCity}</strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">{t("Budget:", "بجٹ:")}</span>
                <strong className="text-navy-900 dark:text-white">{budgetCrores} Crore PKR</strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">{t("Attached Files:", "منسلک فائلیں:")}</span>
                <strong className="text-navy-900 dark:text-white">
                  {(buildingPlanFile ? 1 : 0) + (boqFile ? 1 : 0) + (contractFile ? 1 : 0) + siteImages.length} Files
                </strong>
              </div>
            </div>
          </div>

          {/* Step 3 Actions: Start Audit Button */}
          <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setCurrentStep(2)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all border border-slate-200 dark:border-slate-700"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>{t("Back: Uploads", "پچھلا مرحلہ: فائلیں")}</span>
            </button>

            {/* THE START AUDIT BUTTON */}
            <button
              type="button"
              onClick={handleStartAudit}
              className="inline-flex items-center gap-2.5 px-7 py-3 rounded-xl bg-gradient-to-r from-orange-500 via-orange-600 to-amber-600 hover:from-orange-600 hover:to-amber-700 text-white font-extrabold text-sm sm:text-base shadow-lg shadow-orange-500/25 active:scale-95 transition-all group"
            >
              <Play className="w-4 h-4 fill-white transition-transform group-hover:scale-110" />
              <span>{t("Start Audit", "آڈٹ شروع کریں")}</span>
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* RUNNING AUDIT INTERACTIVE MODAL OVERLAY                                    */}
      {/* ========================================================================= */}
      {isAuditing && (
        <div className="fixed inset-0 z-50 bg-navy-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 p-6 sm:p-8 shadow-2xl space-y-6 text-center">
            {/* Animated Icon */}
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-500 to-amber-600 text-white mx-auto flex items-center justify-center shadow-lg shadow-orange-500/20">
              {auditComplete ? (
                <CheckCircle2 className="w-8 h-8 animate-bounce" />
              ) : (
                <Cpu className="w-8 h-8 animate-pulse" />
              )}
            </div>

            {/* Title & Task */}
            <div className="space-y-2">
              <h3 className="text-lg sm:text-xl font-black text-navy-900 dark:text-white">
                {auditComplete
                  ? t("Audit Analysis Successfully Complete!", "آڈٹ تجزیہ کامیابی کے ساتھ مکمل ہو گیا!")
                  : t("Running TameerAI Construction Audit...", "تعمیر اے آئی کا آڈٹ تجزیہ جاری ہے...")}
              </h3>
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 min-h-[40px] flex items-center justify-center">
                {auditCurrentTask}
              </p>
            </div>

            {/* Progress Bar */}
            <div className="space-y-1.5">
              <div className="w-full h-2.5 rounded-full bg-slate-100 dark:bg-navy-950 overflow-hidden border border-slate-200 dark:border-slate-800">
                <div
                  className="h-full bg-gradient-to-r from-orange-500 to-amber-500 transition-all duration-500"
                  style={{ width: `${auditProgress}%` }}
                />
              </div>
              <div className="flex justify-between text-[11px] font-mono text-slate-400">
                <span>{auditProgress}% Complete</span>
                <span>{auditComplete ? "4 / 4 Modules Done" : "Processing"}</span>
              </div>
            </div>

            {/* Results Snapshot when Complete */}
            {auditComplete ? (
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-left text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-navy-900 dark:text-white">
                    {t("Audit Results Summary:", "نتائج کا خلاصہ:")}
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400">
                    2 Alerts Found
                  </span>
                </div>
                <div className="space-y-1 text-slate-600 dark:text-slate-300 text-[11px]">
                  <p className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400">
                    <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                    <span><strong>PBC 2021 Sec 4.2.1:</strong> Staircase clear width 3.5ft &lt; 4.0ft minimum.</span>
                  </p>
                  <p className="flex items-center gap-1.5 text-blue-600 dark:text-blue-400">
                    <Scale className="w-3.5 h-3.5 flex-shrink-0" />
                    <span><strong>FIDIC Cl. 14:</strong> Delay liquidated damages uncapped in agreement draft.</span>
                  </p>
                  <p className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                    <span><strong>BOQ Rate Audit:</strong> Steel Gr.60 budgeted at market rate within 1.2% margin.</span>
                  </p>
                </div>
              </div>
            ) : null}

            {/* Modal Action Buttons */}
            <div className="pt-2 flex flex-col sm:flex-row gap-2.5">
              {auditComplete ? (
                <>
                  <Link
                    href="/dashboard/projects/PRJ-001"
                    className="flex-1 py-2.5 px-4 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs sm:text-sm text-center shadow-md shadow-orange-500/20 transition-all"
                  >
                    {t("Open Project Workspace →", "پروجیکٹ ورک اسپیس کھولیں →")}
                  </Link>
                  <Link
                    href="/dashboard/ai-assistant"
                    className="flex-1 py-2.5 px-4 rounded-xl bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 font-bold text-xs sm:text-sm text-center transition-all"
                  >
                    {t("Discuss with AI Assistant", "اے آئی اسسٹنٹ سے گفتگو")}
                  </Link>
                </>
              ) : (
                <button
                  type="button"
                  onClick={() => setIsAuditing(false)}
                  className="w-full py-2 text-xs font-medium text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  {t("Cancel / Run in Background", "منسوخ کریں / پس منظر میں چلائیں")}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
