"use client";

import { useState, useEffect } from "react";
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
  PlusCircle,
  FolderOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { projectService } from "@/services/projectService";
import { auditService } from "@/services/auditService";
import { contractService } from "@/services/contractService";
import { Project } from "@/types";

const BUILDING_TYPES = [
  { id: "commercial", en: "Commercial Plaza / Mall", ur: "کمرشل پلازہ / شاپنگ مال", icon: Building2 },
  { id: "residential", en: "Residential (House / Apts)", ur: "رہائشی (مکان / اپارٹمنٹس)", icon: Building2 },
  { id: "mixed_use", en: "Mixed-Use Development", ur: "مخلوط استعمال کی عمارت", icon: Layers },
  { id: "industrial", en: "Industrial / Factory", ur: "صنعتی / فیکٹری", icon: Building2 },
];

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

  // Wizard Step
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);

  // Projects from DB
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("new");

  // Step 1: Project Information
  const [projectName, setProjectName] = useState("");
  const [buildingType, setBuildingType] = useState("commercial");
  const [locationCity, setLocationCity] = useState("Lahore");
  const [locationArea, setLocationArea] = useState("");
  const [budgetCrores, setBudgetCrores] = useState("");
  const [totalCoveredArea, setTotalCoveredArea] = useState("");
  const [floorsCount, setFloorsCount] = useState("");

  // Step 2: Upload Files State
  const [buildingPlanFile, setBuildingPlanFile] = useState<string | null>(null);
  const [boqFile, setBoqFile] = useState<string | null>(null);
  const [contractFile, setContractFile] = useState<string | null>(null);

  // Step 3: Choose Analysis Type
  const [selectedAnalysis, setSelectedAnalysis] = useState<"compliance" | "contract" | "cost" | "full">("compliance");

  // Execution State
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [createdResult, setCreatedResult] = useState<{
    projectId: string;
    auditId?: string;
    contractAnalysisId?: string;
  } | null>(null);

  useEffect(() => {
    async function loadProjects() {
      try {
        const projs = await projectService.getProjects();
        setProjects(projs);
        if (projs.length > 0) {
          const first = projs[0];
          setSelectedProjectId(first.id);
          setProjectName(first.name);
          setLocationCity(first.city || "Lahore");
          setLocationArea(first.location || "");
          if (first.budgetCrore) {
            setBudgetCrores(first.budgetCrore.toString());
          }
        }
      } catch (err) {
        console.error("[AuditPage] Error loading projects:", err);
      }
    }
    loadProjects();
  }, []);

  const handleSelectExistingProject = (projId: string, projsList = projects) => {
    setSelectedProjectId(projId);
    if (projId === "new") {
      setProjectName("");
      setLocationArea("");
      setBudgetCrores("");
      return;
    }
    const found = projsList.find((p) => p.id === projId);
    if (found) {
      setProjectName(found.name);
      setLocationCity(found.city || "Lahore");
      setLocationArea(found.location || "");
      if (found.budgetCrore) {
        setBudgetCrores(found.budgetCrore.toString());
      }
    }
  };

  const handleFileChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    setter: (val: string | null) => void
  ) => {
    const file = e.target.files?.[0];
    if (file) {
      setter(file.name);
    }
  };

  const handleStartAudit = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      let targetProjectId = selectedProjectId;

      // 1. If user chose to create a new project first
      if (selectedProjectId === "new") {
        if (!projectName.trim()) {
          setErrorMessage("Project name is required.");
          setIsSubmitting(false);
          return;
        }

        const budgetNum = parseFloat(budgetCrores || "0");
        const newProj = await projectService.createProject({
          name: projectName.trim(),
          city: (locationCity as any) || "Lahore",
          location: locationArea || "Pakistan",
          type: buildingType,
          budgetCrore: budgetNum > 0 ? budgetNum : 1,
        });

        if (!newProj) {
          throw new Error("Failed to create project record.");
        }
        targetProjectId = newProj.id;
      }

      // 2. Submit the requested audit
      let auditId: string | undefined;
      let contractAnalysisId: string | undefined;

      if (selectedAnalysis === "compliance" || selectedAnalysis === "full") {
        const auditRes = await auditService.createComplianceAudit(targetProjectId, {
          governingCode: "PBC 2021",
          summary: `Compliance audit initiated for ${projectName || "Project"} under Pakistan Building Code 2021.`,
        });
        auditId = auditRes?.id;
      }

      if (selectedAnalysis === "contract" || selectedAnalysis === "full") {
        const contractRes = await contractService.createAnalysis(targetProjectId, {
          contractTitle: contractFile || `${projectName || "Project"} Agreement`,
          standardFormat: "FIDIC Red Book (1999/2017)",
        });
        contractAnalysisId = contractRes?.id;
      }

      setCreatedResult({
        projectId: targetProjectId,
        auditId,
        contractAnalysisId,
      });
    } catch (err: any) {
      console.error("[AuditPage] Audit submission error:", err);
      setErrorMessage(err?.response?.data?.detail || err?.message || "Failed to submit audit.");
    } finally {
      setIsSubmitting(false);
    }
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
              {t("TameerAI Construction Audit", "تعمیر اے آئی تعمیراتی آڈٹ")}
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {t("Grounded in PBC 2021 & FIDIC Standards", "پی بی سی 2021 اور فڈک معیارات پر مبنی")}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white tracking-tight">
            {t("Start New Construction Audit", "نیا تعمیراتی آڈٹ شروع کریں")}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t(
              "Select a project workspace, link blueprint and contract documents, and initiate official compliance and safety checks.",
              "پروجیکٹ منتخب کریں، نقشہ جات و معاہدے منسلک کریں اور سرکاری کوڈز کے تحت آڈٹ کریں۔"
            )}
          </p>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* WIZARD STEPS PROGRESS                                                     */}
      {/* ========================================================================= */}
      <div className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
        <div className="grid grid-cols-3 gap-2 sm:gap-4">
          <button
            onClick={() => setCurrentStep(1)}
            className={cn(
              "flex flex-col sm:flex-row items-center sm:items-start gap-2.5 p-2 sm:p-3 rounded-xl transition-all text-left",
              currentStep === 1
                ? "bg-orange-50 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-800"
                : currentStep > 1
                ? "bg-slate-50 dark:bg-navy-950/40 text-slate-700"
                : "text-slate-400 opacity-70"
            )}
          >
            <div
              className={cn(
                "w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0",
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

          <button
            onClick={() => setCurrentStep(2)}
            className={cn(
              "flex flex-col sm:flex-row items-center sm:items-start gap-2.5 p-2 sm:p-3 rounded-xl transition-all text-left",
              currentStep === 2
                ? "bg-orange-50 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-800"
                : currentStep > 2
                ? "bg-slate-50 dark:bg-navy-950/40 text-slate-700"
                : "text-slate-400 opacity-70"
            )}
          >
            <div
              className={cn(
                "w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0",
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

          <button
            onClick={() => setCurrentStep(3)}
            className={cn(
              "flex flex-col sm:flex-row items-center sm:items-start gap-2.5 p-2 sm:p-3 rounded-xl transition-all text-left",
              currentStep === 3
                ? "bg-orange-50 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-800"
                : "text-slate-400 opacity-70"
            )}
          >
            <div
              className={cn(
                "w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0",
                currentStep === 3 ? "bg-orange-500 text-white" : "bg-slate-200 dark:bg-slate-800 text-slate-500"
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
                {t("Audit Scope & Run", "آڈٹ کا دائرہ و آغاز")}
              </p>
            </div>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* STEP 1: PROJECT INFORMATION                                               */}
      {/* ========================================================================= */}
      {currentStep === 1 && (
        <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-6">
          <div className="space-y-4">
            {/* Existing Project Selector */}
            {projects.length > 0 && (
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800">
                <label className="block text-xs font-bold text-navy-900 dark:text-white mb-2">
                  {t("Select Existing Project Workspace:", "موجودہ پروجیکٹ منتخب کریں:")}
                </label>
                <select
                  value={selectedProjectId}
                  onChange={(e) => handleSelectExistingProject(e.target.value)}
                  className="w-full text-xs font-bold p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-navy-900 text-slate-900 dark:text-white focus:outline-none"
                >
                  <option value="new">{t("+ Create New Project for this Audit", "+ نیا پروجیکٹ بنائیں")}</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.city || "Pakistan"})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Project Name */}
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                {t("Project Name", "منصوبے کا نام")} <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="e.g. Gulberg Commercial Centre"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20"
              />
            </div>

            {/* City & Building Type */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                  {t("Location / City Authority", "شہر و مجاز اتھارٹی")}
                </label>
                <select
                  value={locationCity}
                  onChange={(e) => setLocationCity(e.target.value)}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-800 text-slate-900 dark:text-white focus:outline-none"
                >
                  {PAKISTAN_CITIES.map((c) => (
                    <option key={c.name} value={c.name}>
                      {language === "ur" ? c.nameUrdu : c.name} ({c.authority})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                  {t("Building Typology", "عمارت کی قسم")}
                </label>
                <select
                  value={buildingType}
                  onChange={(e) => setBuildingType(e.target.value)}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-800 text-slate-900 dark:text-white focus:outline-none"
                >
                  {BUILDING_TYPES.map((b) => (
                    <option key={b.id} value={b.id}>
                      {language === "ur" ? b.ur : b.en}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Budget & Covered Area */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                  {t("Estimated Budget (Crore PKR)", "تخمینی بجٹ (کروڑ روپے)")}
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={budgetCrores}
                  onChange={(e) => setBudgetCrores(e.target.value)}
                  placeholder="e.g. 12"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-800 text-slate-900 dark:text-white focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                  {t("Covered Area (Sq.Ft)", "کورڈ ایریا (مربع فٹ)")}
                </label>
                <input
                  type="text"
                  value={totalCoveredArea}
                  onChange={(e) => setTotalCoveredArea(e.target.value)}
                  placeholder="e.g. 45,000"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-800 text-slate-900 dark:text-white focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                  {t("Number of Stories / Floors", "منزلوں کی تعداد")}
                </label>
                <input
                  type="text"
                  value={floorsCount}
                  onChange={(e) => setFloorsCount(e.target.value)}
                  placeholder="e.g. G + 5"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-800 text-slate-900 dark:text-white focus:outline-none"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-100 dark:border-slate-800">
            <button
              onClick={() => setCurrentStep(2)}
              disabled={!projectName.trim()}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white shadow-sm transition-all"
            >
              <span>{t("Continue to Uploads", "اگلا مرحلہ: فائلیں")}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 2: ATTACH DOCUMENTS                                                  */}
      {/* ========================================================================= */}
      {currentStep === 2 && (
        <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-6">
          <div className="space-y-4">
            {/* Architectural Plan */}
            <div className="p-4 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 hover:border-orange-500 transition-all">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-orange-500/10 text-orange-600 dark:text-orange-400 flex items-center justify-center">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-navy-900 dark:text-white">
                      {t("Architectural Plan / Drawing (CAD / PDF)", "آرکیٹیکچرل پلان / نقشہ")}
                    </h4>
                    <p className="text-[11px] text-slate-500">
                      {buildingPlanFile ? buildingPlanFile : t("Optional: Attach floor plan for egress & setback check", "نقشہ منسلک کریں")}
                    </p>
                  </div>
                </div>
                <label className="cursor-pointer px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200">
                  {buildingPlanFile ? t("Change", "تبدیل") : t("Select File", "فائل منتخب کریں")}
                  <input
                    type="file"
                    accept=".pdf,.dwg,.dxf"
                    className="hidden"
                    onChange={(e) => handleFileChange(e, setBuildingPlanFile)}
                  />
                </label>
              </div>
            </div>

            {/* BOQ File */}
            <div className="p-4 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 hover:border-orange-500 transition-all">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                    <FileSpreadsheet className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-navy-900 dark:text-white">
                      {t("Itemized BOQ Schedule (Excel / PDF)", "لاگت و بی او کیو شیڈول")}
                    </h4>
                    <p className="text-[11px] text-slate-500">
                      {boqFile ? boqFile : t("Optional: Attach schedule of rates for market index check", "ریٹس شیڈول منسلک کریں")}
                    </p>
                  </div>
                </div>
                <label className="cursor-pointer px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200">
                  {boqFile ? t("Change", "تبدیل") : t("Select File", "فائل منتخب کریں")}
                  <input
                    type="file"
                    accept=".xlsx,.xls,.csv,.pdf"
                    className="hidden"
                    onChange={(e) => handleFileChange(e, setBoqFile)}
                  />
                </label>
              </div>
            </div>

            {/* Contract Agreement */}
            <div className="p-4 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 hover:border-orange-500 transition-all">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                    <Scale className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-navy-900 dark:text-white">
                      {t("Contract / Subcontract Agreement (PDF / Docx)", "معاہدہ دستاویز")}
                    </h4>
                    <p className="text-[11px] text-slate-500">
                      {contractFile ? contractFile : t("Optional: Attach agreement for FIDIC liability review", "معاہدہ منسلک کریں")}
                    </p>
                  </div>
                </div>
                <label className="cursor-pointer px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200">
                  {contractFile ? t("Change", "تبدیل") : t("Select File", "فائل منتخب کریں")}
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    className="hidden"
                    onChange={(e) => handleFileChange(e, setContractFile)}
                  />
                </label>
              </div>
            </div>
          </div>

          <div className="flex justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
            <button
              onClick={() => setCurrentStep(1)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 dark:hover:bg-navy-800"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>{t("Back", "پیچھے")}</span>
            </button>
            <button
              onClick={() => setCurrentStep(3)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 text-white shadow-sm transition-all"
            >
              <span>{t("Continue to Audit Scope", "اگلا مرحلہ: دائرہ کار")}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 3: AUDIT SCOPE & LAUNCH                                              */}
      {/* ========================================================================= */}
      {currentStep === 3 && (
        <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-6">
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-navy-900 dark:text-white">
              {t("Choose Audit Module", "آڈٹ ماڈیول منتخب کریں")}
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div
                onClick={() => setSelectedAnalysis("compliance")}
                className={cn(
                  "p-4 rounded-xl border cursor-pointer transition-all space-y-2",
                  selectedAnalysis === "compliance"
                    ? "bg-orange-50 dark:bg-orange-950/30 border-orange-500 shadow-xs"
                    : "bg-slate-50 dark:bg-navy-800 border-slate-200 dark:border-slate-700"
                )}
              >
                <div className="w-8 h-8 rounded-lg bg-orange-500 text-white flex items-center justify-center">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <h4 className="text-xs font-bold text-navy-900 dark:text-white">
                  {t("Building Code Compliance", "بلڈنگ کوڈ تعمیل (PBC 2021)")}
                </h4>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  {t(
                    "Check stairs, setbacks, and fire egress against PBC 2021 and local authority bylaws.",
                    "سیڑھی، سیٹ بیکس اور فائر سیفٹی کا معائنہ۔"
                  )}
                </p>
              </div>

              <div
                onClick={() => setSelectedAnalysis("contract")}
                className={cn(
                  "p-4 rounded-xl border cursor-pointer transition-all space-y-2",
                  selectedAnalysis === "contract"
                    ? "bg-orange-50 dark:bg-orange-950/30 border-orange-500 shadow-xs"
                    : "bg-slate-50 dark:bg-navy-800 border-slate-200 dark:border-slate-700"
                )}
              >
                <div className="w-8 h-8 rounded-lg bg-blue-500 text-white flex items-center justify-center">
                  <Scale className="w-4 h-4" />
                </div>
                <h4 className="text-xs font-bold text-navy-900 dark:text-white">
                  {t("FIDIC Contract Risk", "فڈک معاہدہ خطرات")}
                </h4>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  {t(
                    "Assess delay damages, retention conditions, and termination clauses against PEC standard bidding rules.",
                    "تاخیری ہرجانے اور یکطرفہ شرائط کی نشاندہی۔"
                  )}
                </p>
              </div>

              <div
                onClick={() => setSelectedAnalysis("full")}
                className={cn(
                  "p-4 rounded-xl border cursor-pointer transition-all space-y-2",
                  selectedAnalysis === "full"
                    ? "bg-orange-50 dark:bg-orange-950/30 border-orange-500 shadow-xs"
                    : "bg-slate-50 dark:bg-navy-800 border-slate-200 dark:border-slate-700"
                )}
              >
                <div className="w-8 h-8 rounded-lg bg-emerald-500 text-white flex items-center justify-center">
                  <Sparkles className="w-4 h-4" />
                </div>
                <h4 className="text-xs font-bold text-navy-900 dark:text-white">
                  {t("Full Comprehensive Audit", "مکمل جامع آڈٹ (Full 360°)")}
                </h4>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  {t(
                    "Runs both statutory building code compliance and FIDIC legal risk evaluations.",
                    "بلڈنگ کوڈ اور معاہداتی خطرات دونوں کا ہمہ جہتی جائزہ۔"
                  )}
                </p>
              </div>
            </div>
          </div>

          {/* Audit Target Summary */}
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-xs space-y-2">
            <h4 className="font-bold text-navy-900 dark:text-white uppercase tracking-wider text-[11px]">
              {t("Audit Target Summary", "آڈٹ تفصیلات خلاصہ")}
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-slate-600 dark:text-slate-400">
              <div>
                <span className="text-[10px] text-slate-400 block">{t("Project:", "منصوبہ:")}</span>
                <strong className="text-navy-900 dark:text-white">{projectName || "Untitled"}</strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">{t("Authority / City:", "شہر:")}</span>
                <strong className="text-navy-900 dark:text-white">{locationCity}</strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">{t("Typology:", "قسم:")}</span>
                <strong className="text-navy-900 dark:text-white capitalize">{buildingType}</strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">{t("Analysis Scope:", "دائرہ کار:")}</span>
                <strong className="text-navy-900 dark:text-white capitalize">{selectedAnalysis}</strong>
              </div>
            </div>
          </div>

          {errorMessage && (
            <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800 text-xs text-rose-700 dark:text-rose-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Action Button */}
          <div className="flex justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
            <button
              onClick={() => setCurrentStep(2)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 dark:hover:bg-navy-800"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>{t("Back", "پیچھے")}</span>
            </button>
            <button
              onClick={handleStartAudit}
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white shadow-sm transition-all"
            >
              {isSubmitting ? (
                <>
                  <Cpu className="w-4 h-4 animate-spin" />
                  <span>{t("Processing Audit...", "آڈٹ جاری ہے...")}</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  <span>{t("Execute Construction Audit", "آڈٹ شروع کریں")}</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* GENUINE SUCCESS MODAL                                                      */}
      {/* ========================================================================= */}
      {createdResult && (
        <div className="fixed inset-0 z-50 bg-navy-950/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-5 text-center">
            <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-bold text-navy-900 dark:text-white">
                {t("Audit Record Created Successfully!", "آڈٹ ریکارڈ کامیابی سے محفوظ ہو گیا!")}
              </h3>
              <p className="text-xs text-slate-500">
                {t(
                  "The construction audit dossier has been recorded in your workspace database.",
                  "تعمیراتی آڈٹ ریکارڈ آپ کے ڈیٹا بیس میں شامل کر دیا گیا ہے۔"
                )}
              </p>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-left text-xs font-mono space-y-1 text-slate-600 dark:text-slate-300">
              <p>Project ID: {createdResult.projectId}</p>
              {createdResult.auditId && <p>Compliance Audit: {createdResult.auditId}</p>}
              {createdResult.contractAnalysisId && <p>Contract Analysis: {createdResult.contractAnalysisId}</p>}
            </div>

            <div className="flex gap-2">
              <Link
                href="/dashboard/compliance"
                className="flex-1 py-2 px-3 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 text-white text-center shadow-sm"
              >
                {t("View Compliance Page", "کمپلائنس صفحہ دیکھیں")}
              </Link>
              <Link
                href={`/dashboard/projects/${createdResult.projectId}`}
                className="flex-1 py-2 px-3 rounded-xl text-xs font-bold bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-center"
              >
                {t("Open Project", "پروجیکٹ کھولیں")}
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
