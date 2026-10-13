"use client";

import { useState } from "react";
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
  ZoomIn,
  ZoomOut,
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
  RotateCcw,
} from "lucide-react";
import { cn } from "@/lib/utils";

// --- Contract Risk Card Interface ---
interface ContractRiskCard {
  id: string;
  clauseTitle: string;
  clauseTitleUrdu: string;
  fidicReference: string;
  pageNumber: number;
  riskLevel: "high" | "medium" | "low";
  riskLevelLabel: string;
  riskLevelLabelUrdu: string;
  explanation: string;
  explanationUrdu: string;
  recommendation: string;
  recommendationUrdu: string;
  impactMetric: string;
  rawClauseSnippet: string;
}

const CONTRACT_RISKS: ContractRiskCard[] = [
  {
    id: "risk-delay",
    clauseTitle: "Delay Clause (Liquidated Damages)",
    clauseTitleUrdu: "تاخیر کا ہرجانہ شق (Delay Clause)",
    fidicReference: "Sub-Clause 8.7 & Clause 14",
    pageNumber: 12,
    riskLevel: "high",
    riskLevelLabel: "Critical Risk (8/10)",
    riskLevelLabelUrdu: "انتہائی خطرہ (8/10)",
    explanation:
      "Contract imposes liquidated damages of 0.5% of total contract value per day of delay WITHOUT an aggregate liability cap. Standard PEC and FIDIC Red Book guidelines mandate a maximum 10% ceiling. Furthermore, the contractor must file extension-of-time (EOT) claims within an unreasonable 7-day window instead of the standard 28 days.",
    explanationUrdu:
      "معاہدے میں تاخیر پر بغیر کسی حد کے یومیہ 0.5 فیصد جرمانہ عائد کیا گیا ہے، جبکہ فڈک اور پی ای سی کے قواعد زیادہ سے زیادہ 10 فیصد حد مقرر کرتے ہیں۔",
    recommendation:
      "Insert an explicit aggregate delay damages cap of 10% of the Final Contract Price, and extend the EOT notification period to 28 days under FIDIC Sub-Clause 20.1.",
    recommendationUrdu:
      "تاخیر کے جرمانے کی کل حد 10 فیصد مقرر کروائیں اور ای او ٹی نوٹس کی مدت 28 دن تک بڑھائیں۔",
    impactMetric: "Potential Uncapped Liability: PKR 24M+",
    rawClauseSnippet:
      "8.7 Delay Damages: If the Subcontractor fails to complete the Works within the Time for Completion, the Subcontractor shall pay to the Main Contractor 0.5% per day of the Subcontract Price without limitation until Completion...",
  },
  {
    id: "risk-payment",
    clauseTitle: "Payment Terms (Certification & Retention)",
    clauseTitleUrdu: "ادائیگی اور کٹوتی کی شرائط (Payment Terms)",
    fidicReference: "Sub-Clause 14.7 & Clause 14.3",
    pageNumber: 18,
    riskLevel: "high",
    riskLevelLabel: "Severe Cash Flow Risk (8/10)",
    riskLevelLabelUrdu: "کیش فلو کا بڑا خطرہ (8/10)",
    explanation:
      "Payment term is set to 90 days following Interim Payment Certificate (IPC) submission (industry norm is 30–45 days). 10% retention money is contingent upon complete tenant occupancy rather than the Taking-Over Certificate (TOC). No financing markup is stipulated for late employer disbursements.",
    explanationUrdu:
      "بل جمع کروانے کے بعد ادائیگی کی مدت 90 دن رکھی گئی ہے اور 10 فیصد کٹوتی کی واپسی بلا جواز تاخیر کا شکار ہو سکتی ہے۔",
    recommendation:
      "Reduce payment timeline to 30 days post-engineer verification. Negotiate release of 50% retention upon TOC issuance and 50% upon Defect Liability Certificate (DLC). Add KIBOR + 2% late payment interest clause.",
    recommendationUrdu:
      "ادائیگی کی مدت 30 دن تک لائیں اور کائبور پلس 2 فیصد تاخیری سود کی شق شامل کروائیں۔",
    impactMetric: "Working Capital Lockup: 90 Days",
    rawClauseSnippet:
      "14.7 Payment: The Main Contractor shall pay the certified amount within 90 days after receiving the Subcontractor's monthly statement. Retention money shall be held until 100% building tenant occupancy is achieved...",
  },
  {
    id: "risk-termination",
    clauseTitle: "Termination Clause (Unilateral Default)",
    clauseTitleUrdu: "معاہدے کی منسوخی کی شق (Termination Clause)",
    fidicReference: "Sub-Clause 15.2 & Clause 16.2",
    pageNumber: 24,
    riskLevel: "high",
    riskLevelLabel: "High Contractual Risk (7/10)",
    riskLevelLabelUrdu: "اعلیٰ قانونی خطرہ (7/10)",
    explanation:
      "The employer reserves unilateral termination rights 'for convenience' with merely 7 days written notice without obligation to reimburse contractor demobilization costs, site overheads, or materials ordered. Conversely, the contractor's right to suspend works for unpaid certified bills requires an onerous 60-day cure period.",
    explanationUrdu:
      "مالک کو محض 7 دن کے نوٹس پر بغیر اخراجات ادا کیے کام ختم کرنے کا یکطرفہ حق دیا گیا ہے۔",
    recommendation:
      "Require that termination for convenience includes full reimbursement of verified site demobilization costs and materials procurement. Standardize contractor work suspension right after 21 days of non-payment.",
    recommendationUrdu:
      "یکطرفہ منسوخی کی صورت میں سامان اور مشینری کے تمام اخراجات کی واپسی لازم کروائیں۔",
    impactMetric: "Risk of Stranded Equipment & Site Costs",
    rawClauseSnippet:
      "15.2 Termination by Main Contractor: The Main Contractor may terminate this Subcontract at any time for convenience upon giving 7 days written notice. In such event, the Subcontractor shall not be entitled to lost overhead or profit...",
  },
];

export default function ContractAnalyzerPage() {
  const { t, language } = useLanguage();

  // Active Selected Risk Card
  const [selectedRiskId, setSelectedRiskId] = useState<string>("risk-delay");

  // PDF Viewer State
  const [pdfZoom, setPdfZoom] = useState(100);
  const [activePage, setActivePage] = useState(12);

  // Uploaded Contract File State
  const [contractFile, setContractFile] = useState<string>(
    "FIDIC_Subcontract_Agreement_DHA_Plaza_Rev2.pdf"
  );
  const [isUploading, setIsUploading] = useState(false);

  const activeRisk =
    CONTRACT_RISKS.find((r) => r.id === selectedRiskId) || CONTRACT_RISKS[0];

  const handleSelectRisk = (risk: ContractRiskCard) => {
    setSelectedRiskId(risk.id);
    setActivePage(risk.pageNumber);
  };

  const handleSimulatedUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setIsUploading(true);
      setTimeout(() => {
        setContractFile(file.name);
        setIsUploading(false);
      }, 1000);
    }
  };

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
              {t("FIDIC Red Book 2017 & Subcontract Standard", "فڈک ریڈ بک معیارات")}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white tracking-tight flex items-center gap-2.5">
            <Scale className="w-6 h-6 text-orange-500" />
            <span>{t("Contract Analyzer", "معاہدہ تجزیہ کار (Contract Analyzer)")}</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {t(
              "Audits construction contracts, FIDIC subcontracts & contractor agreements for liquidated damages, unfair liability, and cash flow exposure.",
              "تعمیراتی معاہدات کا خودکار تجزیہ، تاخیری جرمانے اور یکطرفہ شرائط کی نشاندہی۔"
            )}
          </p>
        </div>

        {/* Header Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          <Link
            href="/dashboard/audit"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-200 bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 shadow-2xs transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
            <span>{t("New Contract Audit", "نیا معاہدہ آڈٹ")}</span>
          </Link>
          <Link
            href="/dashboard/ai-assistant"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 text-white shadow-sm shadow-orange-500/20 transition-all"
          >
            <Bot className="w-3.5 h-3.5" />
            <span>{t("Ask Legal AI Assistant", "قانونی اے آئی سے پوچھیں")}</span>
          </Link>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* UPLOAD SECTION: FIDIC CONTRACT PDF                                        */}
      {/* ========================================================================= */}
      <div className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3.5 min-w-0">
          <div className="w-12 h-12 rounded-2xl bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 flex items-center justify-center flex-shrink-0">
            <FileText className="w-6 h-6" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-navy-900 dark:text-white truncate">
                {contractFile}
              </h2>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-black uppercase bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                {t("Audited", "جانچ شدہ")}
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {t("48 Clauses scanned · Grounded in FIDIC Red Book 2017 & PEC Bidding Rules", "48 شقوں کا فڈک معیارات پر جائزہ مکمل")}
            </p>
          </div>
        </div>

        {/* Upload Button & File Input */}
        <div className="flex items-center gap-2 flex-shrink-0 w-full md:w-auto justify-end">
          <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 dark:hover:bg-navy-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition-all shadow-2xs">
            <UploadCloud className="w-4 h-4 text-orange-500" />
            <span>{isUploading ? t("Scanning...", "تجزیہ جاری...") : t("Upload Different FIDIC Contract PDF", "دوسرا معاہدہ اپ لوڈ کریں")}</span>
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={handleSimulatedUpload}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* RESULTS TOP ROW: RISK SCORE (8/10) + HIGH RISK METRICS                    */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: RISK SCORE (8/10) */}
        <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {t("Contract Risk Score", "معاہدے کا خطرہ اسکور")}
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl sm:text-4xl font-black text-rose-600 dark:text-rose-400 font-mono tracking-tight">
                8/10
              </span>
              <span className="text-xs font-extrabold uppercase px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                {t("High Risk", "زیادہ خطرہ")}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              {t("Severe contractor liability exposure", "ٹھیکیدار پر غیر منصفانہ مالی بوجھ")}
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 flex items-center justify-center flex-shrink-0">
            <ShieldAlert className="w-6 h-6" />
          </div>
        </div>

        {/* Metric 2: DELAY RISK */}
        <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {t("Delay Liability", "تاخیر کا ہرجانہ")}
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-black text-rose-600 dark:text-rose-400 font-mono">
                Uncapped
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              {t("0.5% / day with NO 10% maximum cap", "یومیہ 0.5 فیصد بغیر کسی حد کے")}
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 flex items-center justify-center flex-shrink-0">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        {/* Metric 3: CASH FLOW RISK */}
        <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {t("Payment Cycle", "ادائیگی کی مدت")}
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-black text-amber-600 dark:text-amber-400 font-mono">
                90 Days
              </span>
              <span className="text-xs text-slate-400">vs 30d norm</span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              {t("Working capital lockup risk", "رقم کی واپسی میں غیر ضروری تاخیر")}
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 flex items-center justify-center flex-shrink-0">
            <Coins className="w-6 h-6" />
          </div>
        </div>

        {/* Metric 4: FAIR CLAUSES */}
        <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {t("Standard Clauses", "منصفانہ شقیں")}
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-black text-emerald-600 dark:text-emerald-400 font-mono">
                43 / 48
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              {t("Complies with PEC & FIDIC standard", "پی ای سی اور فڈک کے مطابق")}
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 flex items-center justify-center flex-shrink-0">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* MAIN TWO-COLUMN SPLIT: 3 RISK CARDS (Left) + PDF PREVIEW VIEWER (Right)   */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* ----------------------------------------------------------------------- */}
        {/* LEFT COLUMN (6 COLS): THE 3 PRIMARY RISK CARDS                          */}
        {/* 1. Delay Clause   2. Payment Terms   3. Termination Clause              */}
        {/* ----------------------------------------------------------------------- */}
        <div className="lg:col-span-6 space-y-4">
          <div className="flex items-center justify-between pb-1">
            <h2 className="text-sm font-bold text-navy-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-500" />
              <span>{t("Critical Risk Findings", "اہم معاہداتی خطرات")}</span>
            </h2>
            <span className="text-xs text-slate-400 font-mono">
              3 High Risk Cards
            </span>
          </div>

          {CONTRACT_RISKS.map((risk) => {
            const isSelected = selectedRiskId === risk.id;

            return (
              <div
                key={risk.id}
                onClick={() => handleSelectRisk(risk)}
                className={cn(
                  "cursor-pointer p-5 rounded-2xl border transition-all space-y-3.5 relative overflow-hidden",
                  isSelected
                    ? "bg-white dark:bg-navy-900 border-rose-500/80 ring-2 ring-rose-500/20 shadow-md"
                    : "bg-white/80 dark:bg-navy-900/80 border-slate-200/80 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 shadow-2xs"
                )}
              >
                {/* Header: Title + Risk Level Badge */}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-rose-500 text-white">
                        {t(risk.riskLevelLabel, risk.riskLevelLabelUrdu)}
                      </span>
                      <span className="text-xs font-mono font-semibold text-slate-400">
                        {risk.fidicReference} · Page {risk.pageNumber}
                      </span>
                    </div>
                    <h3 className="text-base font-extrabold text-navy-900 dark:text-white mt-1">
                      {t(risk.clauseTitle, risk.clauseTitleUrdu)}
                    </h3>
                  </div>

                  <span className="text-[11px] font-bold text-rose-600 dark:text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20 flex-shrink-0">
                    {risk.impactMetric}
                  </span>
                </div>

                {/* EXPLANATION SECTION (Required by prompt) */}
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    {t("Risk Explanation:", "خطرے کی وضاحت (Explanation):")}
                  </span>
                  <p className="text-xs leading-relaxed text-slate-700 dark:text-slate-300">
                    {t(risk.explanation, risk.explanationUrdu)}
                  </p>
                </div>

                {/* RECOMMENDATION SECTION (Required by prompt) */}
                <div className="p-3.5 rounded-xl bg-orange-50/70 dark:bg-orange-950/30 border border-orange-200 dark:border-orange-800/60 space-y-1">
                  <span className="text-[11px] font-black text-orange-900 dark:text-orange-300 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-orange-500" />
                    <span>{t("AI Recommendation & Negotiation Counter-Clause:", "تجویز کردہ ترمیم (Recommendation):")}</span>
                  </span>
                  <p className="text-xs leading-relaxed text-slate-800 dark:text-slate-200 font-medium">
                    {t(risk.recommendation, risk.recommendationUrdu)}
                  </p>
                </div>

                {/* Bottom Actions inside Card */}
                <div className="pt-1 flex items-center justify-between text-xs border-t border-slate-100 dark:border-slate-800/80">
                  <span className="text-slate-400 text-[11px]">
                    {t("Click to highlight on PDF Viewer", "پی ڈی ایف میں شق دیکھنے کے لیے کلک کریں")}
                  </span>
                  <div className="flex items-center gap-2">
                    <Link
                      href={`/dashboard/ai-assistant`}
                      onClick={(e) => e.stopPropagation()}
                      className="text-orange-500 hover:underline font-bold text-[11px] flex items-center gap-1"
                    >
                      <span>{t("Negotiate with AI", "اے آئی سے ڈرافٹ بنائیں")}</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* ----------------------------------------------------------------------- */}
        {/* RIGHT COLUMN (6 COLS): PDF PREVIEW VIEWER                               */}
        {/* ----------------------------------------------------------------------- */}
        <div className="lg:col-span-6 space-y-3">
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-900 overflow-hidden shadow-md flex flex-col">
            {/* PDF Toolbar Header */}
            <div className="p-3 bg-slate-50 dark:bg-navy-950 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between flex-wrap gap-2 text-xs">
              <div className="flex items-center gap-2 min-w-0">
                <FileText className="w-4 h-4 text-orange-500 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="font-bold text-navy-900 dark:text-white truncate text-[11px]">
                    FIDIC_Subcontract_Agreement_DHA_Plaza_Rev2.pdf
                  </p>
                  <p className="text-[10px] text-slate-400">
                    {t(`Page ${activePage} of 64 · Active Clause Highlighted`, `صفحہ ${activePage} از 64 · نمایاں شدہ شق`)}
                  </p>
                </div>
              </div>

              {/* PDF Zoom & Tool Controls */}
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPdfZoom((z) => Math.max(80, z - 10))}
                  className="p-1 rounded text-slate-400 hover:text-navy-900 dark:hover:text-white"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <span className="text-[10px] font-mono text-slate-500 px-1">{pdfZoom}%</span>
                <button
                  onClick={() => setPdfZoom((z) => Math.min(130, z + 10))}
                  className="p-1 rounded text-slate-400 hover:text-navy-900 dark:hover:text-white"
                  title="Zoom In"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setPdfZoom(100)}
                  className="p-1 rounded text-slate-400 hover:text-navy-900 dark:hover:text-white ml-0.5"
                  title="Reset Zoom"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
                <button
                  className="p-1 rounded text-slate-400 hover:text-navy-900 dark:hover:text-white ml-1"
                  title="Download Contract PDF"
                >
                  <Download className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Document Clause Navigator Tabs */}
            <div className="px-3 py-2 bg-slate-100/70 dark:bg-navy-950/70 border-b border-slate-200/80 dark:border-slate-800 flex gap-2 text-[10px] overflow-x-auto scrollbar-none">
              <button
                onClick={() => {
                  setSelectedRiskId("risk-delay");
                  setActivePage(12);
                }}
                className={cn(
                  "px-2.5 py-1 rounded-md font-bold whitespace-nowrap transition-all",
                  selectedRiskId === "risk-delay"
                    ? "bg-rose-500 text-white shadow-xs"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-200/60 dark:hover:bg-slate-800"
                )}
              >
                Cl. 8.7 Delay (p.12)
              </button>
              <button
                onClick={() => {
                  setSelectedRiskId("risk-payment");
                  setActivePage(18);
                }}
                className={cn(
                  "px-2.5 py-1 rounded-md font-bold whitespace-nowrap transition-all",
                  selectedRiskId === "risk-payment"
                    ? "bg-rose-500 text-white shadow-xs"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-200/60 dark:hover:bg-slate-800"
                )}
              >
                Cl. 14.7 Payment (p.18)
              </button>
              <button
                onClick={() => {
                  setSelectedRiskId("risk-termination");
                  setActivePage(24);
                }}
                className={cn(
                  "px-2.5 py-1 rounded-md font-bold whitespace-nowrap transition-all",
                  selectedRiskId === "risk-termination"
                    ? "bg-rose-500 text-white shadow-xs"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-200/60 dark:hover:bg-slate-800"
                )}
              >
                Cl. 15.2 Termination (p.24)
              </button>
            </div>

            {/* Simulated PDF Viewer Paper Sheet */}
            <div className="p-4 sm:p-6 bg-slate-200/70 dark:bg-navy-950 flex justify-center min-h-[480px] max-h-[580px] overflow-y-auto">
              <div
                style={{ transform: `scale(${pdfZoom / 100})`, transformOrigin: "top center" }}
                className="w-full max-w-[420px] bg-white text-slate-900 p-6 shadow-xl rounded-xs border border-slate-300 font-serif text-[11px] leading-relaxed select-text transition-transform duration-200"
              >
                {/* Legal Header */}
                <div className="border-b-2 border-slate-900 pb-2 mb-4 text-center">
                  <div className="text-[8px] font-sans font-bold tracking-widest uppercase text-slate-500">
                    STANDARD CONDITIONS OF SUBCONTRACT FOR CONSTRUCTION
                  </div>
                  <div className="text-[11px] font-sans font-black tracking-tight mt-0.5 text-slate-900">
                    FIDIC RED BOOK FORM (FIRST EDITION / PEC COMPATIBLE)
                  </div>
                  <div className="text-[8px] italic text-slate-400">
                    Contract Agreement Ref: DHA-PLAZA-PKG-02
                  </div>
                </div>

                {/* Legal Body & Dynamic Highlighted Clause */}
                <div className="space-y-3 font-serif">
                  <div className="text-[10px] font-sans font-bold text-slate-800 uppercase tracking-wide">
                    SECTION {activeRisk.fidicReference.toUpperCase()}
                  </div>

                  {/* Red Alert Marker for Active Clause */}
                  <div className="p-3 rounded-xs bg-rose-50 border-2 border-rose-400 ring-2 ring-rose-400/30 text-slate-900 relative">
                    <div className="flex items-center justify-between font-sans font-bold text-[9px] text-rose-700 mb-1">
                      <span>CRITICAL RISK CLAUSE DETECTED</span>
                      <span className="bg-rose-500 text-white px-1.5 py-0.2 rounded-xs text-[8px]">
                        RISK 8/10
                      </span>
                    </div>
                    <p className="text-[10px] italic leading-relaxed text-slate-900">
                      &quot;{activeRisk.rawClauseSnippet}&quot;
                    </p>
                  </div>

                  <p className="text-[10px] text-slate-600 leading-relaxed">
                    8.8 Suspension of Work: The Engineer may at any time instruct the Subcontractor to suspend progress of part or all of the Works. During such suspension, the Subcontractor shall protect, store and secure such part or the Works against any deterioration, loss or damage...
                  </p>

                  <p className="text-[10px] text-slate-600 leading-relaxed">
                    8.9 Consequences of Suspension: If the Subcontractor suffers delay and/or incurs Cost from complying with the Engineer&apos;s instructions under Sub-Clause 8.8, the Subcontractor shall give notice to the Engineer and shall be entitled subject to Sub-Clause 20.1 to an extension of time...
                  </p>

                  <div className="pt-4 text-[8px] text-slate-400 font-sans flex justify-between border-t border-slate-200">
                    <span>FIDIC-SUBCONTRACT-2017</span>
                    <span>Page {activePage} of 64</span>
                  </div>
                </div>
              </div>
            </div>

            {/* PDF Viewer Bottom Status Bar */}
            <div className="p-3 bg-white dark:bg-navy-900 border-t border-slate-200 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400 flex items-center justify-between">
              <span className="text-[11px]">
                {t("Clause highlighted by TameerAI Legal Engine", "تعمیر اے آئی کی جانب سے ہائی لائٹ شدہ شق")}
              </span>
              <button
                onClick={() => alert(`Downloaded full annotated PDF report for ${contractFile}`)}
                className="text-orange-500 hover:underline font-bold text-[11px]"
              >
                {t("Download Annotated PDF", "نشان زدہ پی ڈی ایف ڈاؤن لوڈ کریں")}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
