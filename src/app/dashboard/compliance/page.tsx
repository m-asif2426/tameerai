"use client";

import { useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Info,
  Layers,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Download,
  FileText,
  Sparkles,
  RefreshCw,
  Search,
  Filter,
  Ruler,
  Crosshair,
  Building2,
  ChevronRight,
  ExternalLink,
  SlidersHorizontal,
  Bot,
  Eye,
  RotateCcw,
} from "lucide-react";
import { cn } from "@/lib/utils";

// --- Rule Inspection Item Interface ---
interface ComplianceRuleItem {
  id: string;
  category: "egress" | "structural" | "zoning" | "fire";
  categoryName: string;
  categoryNameUrdu: string;
  title: string;
  titleUrdu: string;
  status: "violation" | "warning" | "passed";
  requiredValue: string;
  currentValue: string;
  variance?: string;
  referenceCode: string;
  referenceClause: string;
  locationGrid: string;
  description: string;
  descriptionUrdu: string;
  remedy: string;
  remedyUrdu: string;
  pinCoordinates: { x: number; y: number }; // Percentage for CAD Blueprint Pin
}

const COMPLIANCE_ITEMS: ComplianceRuleItem[] = [
  {
    id: "RULE-001",
    category: "egress",
    categoryName: "Means of Egress",
    categoryNameUrdu: "اخراج کے راستے",
    title: "Stair Width",
    titleUrdu: "سیڑھی کی چوڑائی (Stair Width)",
    status: "violation",
    requiredValue: "4.0 feet (48 in / 1,220 mm)",
    currentValue: "3.5 feet (42 in / 1,067 mm)",
    variance: "-6.0 inches (-153 mm) Deficit",
    referenceCode: "PBC 2021",
    referenceClause: "Section 4.2.1 (Minimum Stairway Width)",
    locationGrid: "Grid 4B - East Core Stairwell",
    description:
      "Stairway serving an occupant load exceeding 50 persons in commercial occupancy lacks mandatory clear egress width between handrails.",
    descriptionUrdu:
      "کمرشل عمارت میں 50 سے زائد افراد کے انخلا کے لیے سیڑھی کی چوڑائی مطلوبہ 4.0 فٹ سے 6 انچ کم ہے۔",
    remedy:
      "Increase clear width by shifting partition wall along Grid 4B or widen concrete stringer reveal by 6 inches.",
    remedyUrdu:
      "گرڈ 4B کے ساتھ والی دیوار کو پیچھے ہٹا کر سیڑھی کی چوڑائی 4 فٹ تک کریں۔",
    pinCoordinates: { x: 38, y: 35 },
  },
  {
    id: "RULE-002",
    category: "fire",
    categoryName: "Fire & Life Safety",
    categoryNameUrdu: "آگ سے حفاظت",
    title: "Fire Exit Door Rating",
    titleUrdu: "آگ سے بچاؤ کے دروازے کی ریٹنگ",
    status: "violation",
    requiredValue: "2-Hour Fire Resistance (UL/FM)",
    currentValue: "1-Hour Standard Flush Door",
    variance: "1-Hour Deficiency",
    referenceCode: "PBC 2021",
    referenceClause: "Section 4.7.3 & NFPA 80",
    locationGrid: "Grid 2C - Ground Level Egress Corridor",
    description:
      "Egress stair enclosure door must possess a minimum 2-hour fire endurance rating with automatic hydraulic door closers.",
    descriptionUrdu:
      "انخلا کی سیڑھی کا دروازہ کم از کم 2 گھنٹے آگ روکنے کی صلاحیت کا ہونا ضروری ہے۔",
    remedy:
      "Replace with Class B 120-minute fire-rated steel door assembly with panic push-hardware.",
    remedyUrdu:
      "120 منٹ ریٹڈ اسٹیل فائر ڈور اور پینک بار نصب کریں۔",
    pinCoordinates: { x: 62, y: 72 },
  },
  {
    id: "RULE-003",
    category: "egress",
    categoryName: "Means of Egress",
    categoryNameUrdu: "اخراج کے راستے",
    title: "Accessible Ramp Slope",
    titleUrdu: "ریمپ کی ڈھلوان (Ramp Slope)",
    status: "warning",
    requiredValue: "1:12 (8.33% slope maximum)",
    currentValue: "1:10 (10.0% steep incline)",
    variance: "+1.67% Steeper than code",
    referenceCode: "PBC 2021",
    referenceClause: "Section 4.6.2 (Barrier-Free Access)",
    locationGrid: "Grid 1A - Main Entrance Portico",
    description:
      "Entrance disability access ramp exceeds the maximum allowed gradient slope under accessibility bylaws.",
    descriptionUrdu:
      "مین گیٹ ریمپ کی ڈھلوان معذور افراد کے بین الاقوامی معیار سے زیادہ کھڑی ہے۔",
    remedy:
      "Extend ramp transition run by 3.2 feet to achieve 1:12 standard gradient ratio.",
    remedyUrdu:
      "ریمپ کی لمبائی 3.2 فٹ بڑھا کر 1:12 کا تناسب حاصل کریں۔",
    pinCoordinates: { x: 18, y: 78 },
  },
  {
    id: "RULE-004",
    category: "structural",
    categoryName: "Structural Framing",
    categoryNameUrdu: "سٹرکچرل فریم",
    title: "Column Tie Spacing",
    titleUrdu: "کالم ٹائی اسپیسنگ",
    status: "warning",
    requiredValue: "100 mm c/c (Critical Joint Zone)",
    currentValue: "150 mm c/c Uniform Spacing",
    variance: "+50 mm over maximum tie pitch",
    referenceCode: "PBC 2021",
    referenceClause: "Section 5.3.4 (Seismic Zone 2B Ductile Detailing)",
    locationGrid: "Grid 3C - Columns C3 & C4",
    description:
      "Tie stirrup spacing within beam-column connection confines must be densified to 100mm to resist shear hinges in earthquake zone 2B.",
    descriptionUrdu:
      "بیم اور کالم کے جوڑ پر رنگوں کا درمیانی فاصلہ 100 ملی میٹر ہونا چاہیے۔",
    remedy:
      "Add 3 extra 10mm stirrups within 450mm from beam interface top and bottom.",
    remedyUrdu:
      "جوڑ کے پاس اضافی رنگ باندھ کر فاصلہ کم کریں۔",
    pinCoordinates: { x: 55, y: 44 },
  },
  {
    id: "RULE-005",
    category: "zoning",
    categoryName: "Zoning & Setbacks",
    categoryNameUrdu: "سیٹ بیک اور زوننگ",
    title: "Rear Setback Buffer",
    titleUrdu: "پچھلا سیٹ بیک (Rear Setback)",
    status: "warning",
    requiredValue: "15.0 ft clear buffer",
    currentValue: "14.2 ft (Canopy projection)",
    variance: "-0.8 ft encroachment",
    referenceCode: "LDA Bylaws 2020",
    referenceClause: "Clause 19(c) Commercial Buildings",
    locationGrid: "Grid 6D - Rear Property Line",
    description:
      "HVAC condenser cantilever platform slightly overhangs the mandatory 15-foot rear open space.",
    descriptionUrdu:
      "اے سی پلیٹ فارم پچھلے سیٹ بیک کے اندر 0.8 فٹ تجاوز کر رہا ہے۔",
    remedy:
      "Relocate condenser brackets to rooftop or recess within wall reveal.",
    remedyUrdu:
      "اے سی بریکٹس چھت پر منتقل کریں۔",
    pinCoordinates: { x: 82, y: 22 },
  },
  {
    id: "RULE-006",
    category: "structural",
    categoryName: "Structural Framing",
    categoryNameUrdu: "سٹرکچرل فریم",
    title: "Column Minimum Size",
    titleUrdu: "کالم کا کم از کم سائز",
    status: "passed",
    requiredValue: "300 × 300 mm minimum",
    currentValue: "350 × 350 mm Reinforced",
    variance: "+50 mm Safe Margin",
    referenceCode: "PBC 2021",
    referenceClause: "Section 5.1.2 & ACI 318-19",
    locationGrid: "All Perimeter Columns (Grid 1A-6D)",
    description: "Square reinforced concrete columns satisfy structural compression and tributary area load.",
    descriptionUrdu: "تمام بیرونی کالم مطلوبہ سائز سے بڑے اور محفوظ ہیں۔",
    remedy: "Compliant. No action required.",
    remedyUrdu: "مکمل درست۔",
    pinCoordinates: { x: 25, y: 25 },
  },
  {
    id: "RULE-007",
    category: "egress",
    categoryName: "Means of Egress",
    categoryNameUrdu: "اخراج کے راستے",
    title: "Exit Travel Distance",
    titleUrdu: "انخلا کا فاصلہ (Travel Distance)",
    status: "passed",
    requiredValue: "150 ft maximum with sprinklers",
    currentValue: "88 ft measured path",
    variance: "-62 ft well within threshold",
    referenceCode: "PBC 2021",
    referenceClause: "Section 4.4.1 (Common Path of Travel)",
    locationGrid: "Floor 2 - Entire Tenant Floor",
    description: "Maximum distance from any occupiable point to the nearest enclosed exit stairway is fully compliant.",
    descriptionUrdu: "کسی بھی کمرے سے سیڑھی تک کا فاصلہ حد کے اندر ہے۔",
    remedy: "Compliant. No action required.",
    remedyUrdu: "مکمل درست۔",
    pinCoordinates: { x: 70, y: 50 },
  },
  {
    id: "RULE-008",
    category: "zoning",
    categoryName: "Zoning & Setbacks",
    categoryNameUrdu: "سیٹ بیک اور زوننگ",
    title: "Front Road Setback",
    titleUrdu: "سامنے والا روڈ سیٹ بیک",
    status: "passed",
    requiredValue: "20.0 ft from Main Boulevard",
    currentValue: "22.5 ft dedicated buffer",
    variance: "+2.5 ft extra setback buffer",
    referenceCode: "DHA Planning 2023",
    referenceClause: "Chapter 3 Commercial Corridors",
    locationGrid: "Grid 1A-1D - Front Façade",
    description: "Front pedestrian plaza and landscaping exceed mandatory clearance from road right-of-way.",
    descriptionUrdu: "سامنے کا سیٹ بیک قواعد کے عین مطابق ہے۔",
    remedy: "Compliant. No action required.",
    remedyUrdu: "مکمل درست۔",
    pinCoordinates: { x: 15, y: 88 },
  },
  {
    id: "RULE-009",
    category: "structural",
    categoryName: "Structural Framing",
    categoryNameUrdu: "سٹرکچرل فریم",
    title: "Foundation Embedment Depth",
    titleUrdu: "بنیاد کی گہرائی (Embedment Depth)",
    status: "passed",
    requiredValue: "6.0 ft below finished ground level",
    currentValue: "7.5 ft raft footing depth",
    variance: "+1.5 ft depth in dense gravel stratum",
    referenceCode: "PBC 2021",
    referenceClause: "Section 3.2.1 (Foundation Geotechnical)",
    locationGrid: "Substructure Raft Bed",
    description: "Bearing layer rests on tested firm gravel stratum with allowable soil capacity of 1.75 tsf.",
    descriptionUrdu: "بنیاد کی گہرائی مٹی کی برداشت کے مطابق تسلی بخش ہے۔",
    remedy: "Compliant. No action required.",
    remedyUrdu: "مکمل درست۔",
    pinCoordinates: { x: 45, y: 80 },
  },
];

export default function CompliancePage() {
  const { t, language } = useLanguage();

  // Selected Rule for Inspection Modal/Detail Panel
  const [selectedRuleId, setSelectedRuleId] = useState<string>("RULE-001");
  const [filterCategory, setFilterCategory] = useState<"all" | "violation" | "warning" | "passed">("all");
  const [searchQuery, setSearchQuery] = useState("");

  // CAD Blueprint Viewer Controls
  const [cadZoom, setCadZoom] = useState(100);
  const [showGrid, setShowGrid] = useState(true);
  const [showDimensions, setShowDimensions] = useState(true);
  const [showDefectPins, setShowDefectPins] = useState(true);

  // Active Selected Rule Object
  const activeRule = COMPLIANCE_ITEMS.find((r) => r.id === selectedRuleId) || COMPLIANCE_ITEMS[0];

  // Filtered Rules
  const filteredRules = COMPLIANCE_ITEMS.filter((item) => {
    const matchesFilter = filterCategory === "all" || item.status === filterCategory;
    const matchesSearch =
      !searchQuery ||
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.referenceCode.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.locationGrid.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  // Summary counts
  const passedCount = 48; // Standard 48 passed items
  const warningsCount = 3;
  const violationsCount = 2;
  const complianceScore = 92; // 92% requested by user

  return (
    <div className="space-y-6 pb-12 font-sans">
      {/* ========================================================================= */}
      {/* TOP HEADER & CONTROLS                                                     */}
      {/* ========================================================================= */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20">
              {t("PBC 2021 Automated Rule Checker", "پی بی سی 2021 خودکار رول چیکر")}
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {t("Project: DHA Commercial Plaza (Level 2 Plan)", "منصوبہ: ڈی ایچ اے کمرشل پلازہ")}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white tracking-tight flex items-center gap-2.5">
            <ShieldCheck className="w-6 h-6 text-orange-500" />
            <span>{t("Compliance Analysis", "تعمیل کا تجزیہ (Compliance Analysis)")}</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {t(
              "Deep algorithmic audit of architectural CAD drawings and structural plans against Pakistan Building Code 2021 & LDA By-laws.",
              "پاکستان بلڈنگ کوڈ 2021 اور ایل ڈی اے قوانین کے تحت نقشہ جات کا خودکار انجینئرنگ معائنہ۔"
            )}
          </p>
        </div>

        {/* Top Action Toolbar */}
        <div className="flex items-center gap-2 flex-wrap">
          <Link
            href="/dashboard/audit"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-200 bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 shadow-2xs transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
            <span>{t("Re-Run Audit", "دوبارہ آڈٹ کریں")}</span>
          </Link>
          <Link
            href="/dashboard/ai-assistant"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 text-white shadow-sm shadow-orange-500/20 transition-all"
          >
            <Bot className="w-3.5 h-3.5" />
            <span>{t("Ask AI Assistant", "اے آئی سے پوچھیں")}</span>
          </Link>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 4 SUMMARY STATS: COMPLIANCE SCORE (92%) + PASSED + WARNINGS + VIOLATIONS   */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: COMPLIANCE SCORE (92%) */}
        <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs relative overflow-hidden flex items-center justify-between">
          <div className="space-y-1 z-10">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {t("Compliance Score", "مجموعی تعمیل اسکور")}
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl sm:text-4xl font-black text-navy-900 dark:text-white font-mono tracking-tight">
                {complianceScore}%
              </span>
              <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
                +4% vs Rev 2
              </span>
            </div>
            <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400">
              {t("High Compliance · Minor Deficits", "اعلیٰ تعمیل · معمولی نقائص")}
            </p>
          </div>

          {/* Radial Gauge Visual */}
          <div className="relative w-16 h-16 flex items-center justify-center flex-shrink-0">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-slate-100 dark:text-slate-800"
                strokeWidth="3.5"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="text-orange-500"
                strokeDasharray="92, 100"
                strokeWidth="3.5"
                strokeLinecap="round"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <ShieldCheck className="w-5 h-5 text-orange-500 absolute" />
          </div>
        </div>

        {/* Card 2: PASSED ITEMS */}
        <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {t("Passed Items", "کامیاب شقیں (Passed)")}
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-black text-emerald-600 dark:text-emerald-400 font-mono">
                {passedCount}
              </span>
              <span className="text-xs text-slate-400">/ 53 {t("Rules", "شقیں")}</span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              {t("Structural, Egress distance & footing", "سٹرکچر، فاصلہ اور فاؤنڈیشن درست")}
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 flex items-center justify-center flex-shrink-0">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        {/* Card 3: WARNINGS */}
        <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {t("Warnings", "انتباہات (Warnings)")}
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-black text-amber-600 dark:text-amber-400 font-mono">
                {warningsCount}
              </span>
              <span className="text-xs text-amber-600/80 font-bold">{t("Need Review", "جائزہ طلب")}</span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              {t("Ramp slope, tie pitch & rear canopy", "ریمپ ڈھلوان، ٹائی اور سیٹ بیک")}
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

        {/* Card 4: VIOLATIONS */}
        <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {t("Violations", "خلاف ورزیاں (Violations)")}
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-black text-rose-600 dark:text-rose-400 font-mono">
                {violationsCount}
              </span>
              <span className="text-xs font-bold text-rose-600 dark:text-rose-400 bg-rose-500/10 px-1.5 py-0.5 rounded">
                Critical
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              {t("Stair clear width & fire exit rating", "سیڑھی چوڑائی اور فائر ڈور ریٹنگ")}
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 flex items-center justify-center flex-shrink-0">
            <XCircle className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* MAIN TWO-COLUMN SPLIT: BLUEPRINT CAD VIEWER (Left) + RULE INSPECTOR (Right) */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* ----------------------------------------------------------------------- */}
        {/* LEFT COLUMN (7 COLS): ENGINEERING BLUEPRINT PREVIEW                     */}
        {/* ----------------------------------------------------------------------- */}
        <div className="lg:col-span-7 space-y-3">
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-navy-950 text-white overflow-hidden shadow-md flex flex-col">
            {/* CAD Toolbar Header */}
            <div className="p-3 bg-navy-900/90 border-b border-navy-800 flex items-center justify-between flex-wrap gap-2 text-xs">
              <div className="flex items-center gap-2 min-w-0">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse flex-shrink-0" />
                <span className="font-mono font-bold text-slate-200 truncate text-[11px]">
                  DHA_COMM_PLAZA_LVL2_EGRESS_PLAN_REV4.dwg
                </span>
                <span className="hidden sm:inline-block px-1.5 py-0.5 rounded text-[9px] font-mono bg-navy-800 text-slate-400 border border-navy-700">
                  Scale: 1:100 (1/4&quot; = 1&apos;-0&quot;)
                </span>
              </div>

              {/* Viewer Controls */}
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => setShowGrid(!showGrid)}
                  className={cn(
                    "p-1.5 rounded-lg text-xs font-mono transition-colors",
                    showGrid ? "bg-orange-500/20 text-orange-400 border border-orange-500/30" : "text-slate-400 hover:text-white"
                  )}
                  title="Toggle CAD Grid"
                >
                  <Crosshair className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setShowDimensions(!showDimensions)}
                  className={cn(
                    "p-1.5 rounded-lg text-xs font-mono transition-colors",
                    showDimensions ? "bg-orange-500/20 text-orange-400 border border-orange-500/30" : "text-slate-400 hover:text-white"
                  )}
                  title="Toggle Dimension Callouts"
                >
                  <Ruler className="w-3.5 h-3.5" />
                </button>
                <span className="text-slate-700">|</span>
                <button
                  onClick={() => setCadZoom((z) => Math.max(80, z - 10))}
                  className="p-1.5 rounded text-slate-400 hover:text-white"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <span className="text-[10px] font-mono text-slate-400 px-1">{cadZoom}%</span>
                <button
                  onClick={() => setCadZoom((z) => Math.min(140, z + 10))}
                  className="p-1.5 rounded text-slate-400 hover:text-white"
                  title="Zoom In"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setCadZoom(100)}
                  className="p-1.5 rounded text-slate-400 hover:text-white"
                  title="Reset Zoom"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* CAD Interactive Canvas Area */}
            <div className="relative w-full aspect-[4/3] min-h-[380px] sm:min-h-[460px] bg-[#071324] overflow-hidden select-none flex items-center justify-center p-4">
              {/* CAD Subtle Blueprint Grid Pattern */}
              {showGrid && (
                <div
                  className="absolute inset-0 opacity-20 pointer-events-none"
                  style={{
                    backgroundImage:
                      "linear-gradient(to right, #38bdf8 1px, transparent 1px), linear-gradient(to bottom, #38bdf8 1px, transparent 1px)",
                    backgroundSize: "32px 32px",
                  }}
                />
              )}

              {/* Zoomable Vector Architectural Layout Container */}
              <div
                style={{ transform: `scale(${cadZoom / 100})`, transformOrigin: "center" }}
                className="relative w-full h-full max-w-[620px] max-h-[440px] transition-transform duration-200"
              >
                {/* SVG Blueprint Vector Lines */}
                <svg
                  viewBox="0 0 600 420"
                  className="w-full h-full drop-shadow-lg"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  {/* Outer Building Boundary Walls */}
                  <rect
                    x="50"
                    y="40"
                    width="500"
                    height="340"
                    fill="#0a1a33"
                    stroke="#38bdf8"
                    strokeWidth="3.5"
                    rx="4"
                  />

                  {/* Structural Columns Grid (Grey squares) */}
                  {[
                    [60, 50], [220, 50], [380, 50], [530, 50],
                    [60, 200], [220, 200], [380, 200], [530, 200],
                    [60, 360], [220, 360], [380, 360], [530, 360],
                  ].map(([cx, cy], i) => (
                    <rect
                      key={i}
                      x={cx - 8}
                      y={cy - 8}
                      width="16"
                      height="16"
                      fill="#1e293b"
                      stroke="#94a3b8"
                      strokeWidth="1.5"
                    />
                  ))}

                  {/* Main Corridor Hallway */}
                  <line x1="50" y1="210" x2="550" y2="210" stroke="#0ea5e9" strokeWidth="2" strokeDasharray="4,4" />
                  <line x1="300" y1="40" x2="300" y2="380" stroke="#0ea5e9" strokeWidth="2" strokeDasharray="4,4" />

                  {/* STAIRWELL #1 (VIOLATION LOCATION - Grid 4B) */}
                  <g className="cursor-pointer" onClick={() => setSelectedRuleId("RULE-001")}>
                    {/* Stair enclosure room */}
                    <rect
                      x="180"
                      y="70"
                      width="110"
                      height="110"
                      fill={selectedRuleId === "RULE-001" ? "#451a03" : "#172554"}
                      stroke={selectedRuleId === "RULE-001" ? "#f97316" : "#f43f5e"}
                      strokeWidth="2.5"
                      strokeDasharray={selectedRuleId === "RULE-001" ? "none" : "2,2"}
                    />
                    {/* Stair Treads Steps */}
                    {[85, 97, 109, 121, 133, 145, 157].map((stepY, idx) => (
                      <line
                        key={idx}
                        x1="190"
                        y1={stepY}
                        x2="280"
                        y2={stepY}
                        stroke="#f43f5e"
                        strokeWidth="1.5"
                      />
                    ))}
                    {/* Stair Direction Arrow */}
                    <line x1="235" y1="165" x2="235" y2="85" stroke="#fb7185" strokeWidth="2" />
                    <polygon points="235,78 231,88 239,88" fill="#fb7185" />

                    {/* Stair Label */}
                    <text x="200" y="105" fill="#fecdd3" fontSize="11" fontFamily="monospace" fontWeight="bold">
                      STAIR-01
                    </text>
                    <text x="195" y="125" fill="#f43f5e" fontSize="10" fontFamily="monospace" fontWeight="bold">
                      W: 3.5&apos; [42&quot;]
                    </text>
                  </g>

                  {/* Secondary Emergency Exit (Grid 2C) */}
                  <g className="cursor-pointer" onClick={() => setSelectedRuleId("RULE-002")}>
                    <rect
                      x="340"
                      y="260"
                      width="90"
                      height="80"
                      fill="#172554"
                      stroke="#f43f5e"
                      strokeWidth="2"
                    />
                    <path d="M 385 340 A 35 35 0 0 1 420 305" fill="none" stroke="#f43f5e" strokeWidth="2" />
                    <line x1="385" y1="340" x2="420" y2="340" stroke="#f43f5e" strokeWidth="2" />
                    <text x="355" y="290" fill="#fecdd3" fontSize="9" fontFamily="monospace">
                      FIRE EXIT
                    </text>
                    <text x="355" y="302" fill="#fb7185" fontSize="8" fontFamily="monospace">
                      1-HR DOOR
                    </text>
                  </g>

                  {/* Ramp at Entrance (Grid 1A) */}
                  <g className="cursor-pointer" onClick={() => setSelectedRuleId("RULE-003")}>
                    <rect
                      x="80"
                      y="300"
                      width="60"
                      height="60"
                      fill="#1e1b4b"
                      stroke="#fbbf24"
                      strokeWidth="2"
                    />
                    <line x1="80" y1="360" x2="140" y2="300" stroke="#fbbf24" strokeWidth="1.5" />
                    <text x="88" y="325" fill="#fef08a" fontSize="8" fontFamily="monospace">
                      RAMP 1:10
                    </text>
                  </g>

                  {/* Dimension Callouts if enabled */}
                  {showDimensions && (
                    <g fill="#38bdf8" fontSize="9" fontFamily="monospace">
                      {/* Top Overall Dimension */}
                      <line x1="50" y1="25" x2="550" y2="25" stroke="#38bdf8" strokeWidth="1" />
                      <line x1="50" y1="20" x2="50" y2="30" stroke="#38bdf8" strokeWidth="1" />
                      <line x1="550" y1="20" x2="550" y2="30" stroke="#38bdf8" strokeWidth="1" />
                      <text x="275" y="20" textAnchor="middle" fill="#7dd3fc">
                        125&apos;-0&quot; [38.1m]
                      </text>

                      {/* Left Side Dimension */}
                      <line x1="30" y1="40" x2="30" y2="380" stroke="#38bdf8" strokeWidth="1" />
                      <line x1="25" y1="40" x2="35" y2="40" stroke="#38bdf8" strokeWidth="1" />
                      <line x1="25" y1="380" x2="35" y2="380" stroke="#38bdf8" strokeWidth="1" />
                      <text x="18" y="215" textAnchor="middle" transform="rotate(-90 18 215)" fill="#7dd3fc">
                        85&apos;-0&quot; [25.9m]
                      </text>

                      {/* Staircase Deficit Dimension Callout (RED) */}
                      <line x1="180" y1="60" x2="290" y2="60" stroke="#f43f5e" strokeWidth="1.5" />
                      <line x1="180" y1="55" x2="180" y2="65" stroke="#f43f5e" strokeWidth="1.5" />
                      <line x1="290" y1="55" x2="290" y2="65" stroke="#f43f5e" strokeWidth="1.5" />
                      <text x="235" y="53" textAnchor="middle" fill="#f43f5e" fontWeight="bold">
                        3&apos;-6&quot; (REQ: 4&apos;-0&quot;)
                      </text>
                    </g>
                  )}

                  {/* Grid Lines Labels */}
                  <g fill="#94a3b8" fontSize="8" fontFamily="monospace">
                    <text x="50" y="405">GRID 1A</text>
                    <text x="220" y="405">GRID 3B</text>
                    <text x="380" y="405">GRID 4C</text>
                    <text x="525" y="405">GRID 6D</text>
                  </g>
                </svg>

                {/* Interactive Dynamic HTML Defect Pins */}
                {showDefectPins &&
                  COMPLIANCE_ITEMS.map((item) => {
                    const isSelected = selectedRuleId === item.id;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => setSelectedRuleId(item.id)}
                        style={{
                          left: `${item.pinCoordinates.x}%`,
                          top: `${item.pinCoordinates.y}%`,
                        }}
                        className={cn(
                          "absolute -translate-x-1/2 -translate-y-1/2 rounded-full flex items-center justify-center transition-all cursor-pointer z-10",
                          item.status === "violation"
                            ? "bg-rose-500 text-white shadow-lg shadow-rose-500/50"
                            : item.status === "warning"
                            ? "bg-amber-500 text-white shadow-md shadow-amber-500/40"
                            : "bg-emerald-500 text-white shadow-xs",
                          isSelected
                            ? "w-8 h-8 ring-4 ring-white ring-offset-2 ring-offset-navy-950 scale-125 z-20"
                            : "w-6 h-6 hover:scale-110"
                        )}
                        title={`${item.title} (${item.status})`}
                      >
                        {item.status === "violation" ? (
                          <XCircle className="w-3.5 h-3.5" />
                        ) : item.status === "warning" ? (
                          <AlertTriangle className="w-3.5 h-3.5" />
                        ) : (
                          <CheckCircle2 className="w-3.5 h-3.5" />
                        )}
                      </button>
                    );
                  })}
              </div>

              {/* Floating Blueprint Legend Badge */}
              <div className="absolute bottom-3 left-3 bg-navy-900/90 backdrop-blur-md border border-navy-800 rounded-xl p-2.5 text-[10px] text-slate-300 space-y-1 shadow-lg">
                <div className="font-mono font-bold text-slate-400 uppercase tracking-wider mb-1">
                  CAD Markup Legend
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                  <span>Violation (Critical Egress)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                  <span>Warning (Code Review)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <span>Compliant Component</span>
                </div>
              </div>
            </div>

            {/* CAD Viewer Bottom Metadata Footer */}
            <div className="p-3 bg-navy-900/90 border-t border-navy-800 flex items-center justify-between text-xs text-slate-400">
              <span className="font-mono text-[11px]">
                Active Focus: <strong className="text-white">{activeRule.title}</strong> ({activeRule.locationGrid})
              </span>
              <button
                onClick={() => {
                  setCadZoom(100);
                  setShowGrid(true);
                  setShowDimensions(true);
                }}
                className="text-orange-400 hover:underline text-[11px] font-semibold"
              >
                {t("Fit to Screen", "اسکرین پر فٹ کریں")}
              </button>
            </div>
          </div>
        </div>

        {/* ----------------------------------------------------------------------- */}
        {/* RIGHT COLUMN (5 COLS): VIOLATION INSPECTOR & RULE CHECKLIST             */}
        {/* ----------------------------------------------------------------------- */}
        <div className="lg:col-span-5 space-y-4">
          {/* ===================================================================== */}
          {/* THE HIGHLIGHTED VIOLATION CARD: STAIR WIDTH (Required by prompt)      */}
          {/* ===================================================================== */}
          <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border-2 border-rose-500/50 dark:border-rose-500/40 shadow-sm space-y-4 relative overflow-hidden">
            {/* Top Badge & Header */}
            <div className="flex items-start justify-between gap-2 pb-3 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 flex items-center justify-center flex-shrink-0">
                  <XCircle className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full bg-rose-500 text-white">
                      Violation #1
                    </span>
                    <span className="text-xs font-mono text-slate-400">{activeRule.locationGrid}</span>
                  </div>
                  <h3 className="text-base font-extrabold text-navy-900 dark:text-white mt-0.5">
                    {t(activeRule.title, activeRule.titleUrdu)}
                  </h3>
                </div>
              </div>

              <span className="text-[10px] font-mono font-bold text-slate-400">
                {activeRule.id}
              </span>
            </div>

            {/* REQUIRED VS CURRENT MATRIX (Exact prompt values: 4 ft vs 3.5 ft, PBC 2021) */}
            <div className="grid grid-cols-2 gap-2.5 text-xs">
              {/* Required Box */}
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  {t("Required by Code", "مطلوبہ سائز")}
                </span>
                <p className="text-base font-black text-emerald-600 dark:text-emerald-400 font-mono mt-0.5">
                  {activeRule.requiredValue}
                </p>
                <span className="text-[10px] text-slate-500 mt-0.5 block">
                  {t("Clear egress path", "صاف راستہ")}
                </span>
              </div>

              {/* Current Box */}
              <div className="p-3 rounded-xl bg-rose-50/70 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50">
                <span className="text-[10px] font-bold text-rose-700 dark:text-rose-400 uppercase tracking-wider block">
                  {t("Current in Drawing", "ڈرائنگ میں موجود")}
                </span>
                <p className="text-base font-black text-rose-600 dark:text-rose-400 font-mono mt-0.5">
                  {activeRule.currentValue}
                </p>
                <span className="text-[10px] font-bold text-rose-700 dark:text-rose-400 mt-0.5 block">
                  {activeRule.variance}
                </span>
              </div>
            </div>

            {/* Code Reference Callout */}
            <div className="p-3 rounded-xl bg-slate-100 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-orange-500 flex-shrink-0" />
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    {t("Legal & Engineering Reference", "قانونی و تکنیکی حوالہ")}
                  </span>
                  <span className="font-bold text-navy-900 dark:text-white">
                    {activeRule.referenceCode} — {activeRule.referenceClause}
                  </span>
                </div>
              </div>
              <Link
                href="/dashboard/ai-assistant"
                className="text-[11px] font-bold text-orange-500 hover:underline flex items-center gap-1"
              >
                <span>{t("View Clause", "شق دیکھیں")}</span>
                <ExternalLink className="w-3 h-3" />
              </Link>
            </div>

            {/* Description & Engineering Recommendation */}
            <div className="space-y-2 text-xs">
              <div>
                <span className="font-bold text-navy-900 dark:text-white block">
                  {t("Issue Description:", "مسئلے کی تفصیل:")}
                </span>
                <p className="text-slate-600 dark:text-slate-300 mt-0.5 leading-relaxed">
                  {t(activeRule.description, activeRule.descriptionUrdu)}
                </p>
              </div>

              <div className="p-3 rounded-xl bg-orange-50 dark:bg-orange-950/30 border border-orange-200 dark:border-orange-800/60">
                <span className="font-bold text-orange-900 dark:text-orange-300 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-orange-500" />
                  <span>{t("AI Recommended Remedy:", "تجویز کردہ حل:")}</span>
                </span>
                <p className="text-slate-700 dark:text-slate-300 mt-1 leading-relaxed">
                  {t(activeRule.remedy, activeRule.remedyUrdu)}
                </p>
              </div>
            </div>

            {/* Card Action Buttons */}
            <div className="pt-2 flex flex-col sm:flex-row gap-2">
              <Link
                href="/dashboard/ai-assistant"
                className="flex-1 py-2 px-3 rounded-xl bg-orange-500 hover:bg-orange-600 text-white text-xs font-bold text-center transition-all shadow-xs"
              >
                {t("Ask AI to Solve Staircase →", "اے آئی سے متبادل حل پوچھیں →")}
              </Link>
              <button
                type="button"
                onClick={() => alert(`Marking ${activeRule.title} on CAD layer...`)}
                className="py-2 px-3 rounded-xl bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300 text-xs font-semibold text-center transition-all"
              >
                {t("Export CAD Annotation", "سی اے ڈی مارک اپ")}
              </button>
            </div>
          </div>

          {/* ===================================================================== */}
          {/* RULE ITEMS FILTERABLE CHECKLIST                                       */}
          {/* ===================================================================== */}
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-900 p-4 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-navy-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
                <SlidersHorizontal className="w-3.5 h-3.5 text-orange-500" />
                <span>{t("Rule Checklist & Filters", "تمام قواعد کی فہرست")}</span>
              </h3>
              <span className="text-[11px] font-mono text-slate-400">
                {filteredRules.length} of {COMPLIANCE_ITEMS.length} Rules
              </span>
            </div>

            {/* Filter Pills */}
            <div className="flex gap-1.5 overflow-x-auto pb-1 text-xs">
              <button
                onClick={() => setFilterCategory("all")}
                className={cn(
                  "px-2.5 py-1 rounded-lg font-bold text-[11px] transition-all",
                  filterCategory === "all"
                    ? "bg-navy-900 text-white dark:bg-white dark:text-navy-900"
                    : "bg-slate-100 dark:bg-navy-950 text-slate-600 dark:text-slate-400"
                )}
              >
                All (53)
              </button>
              <button
                onClick={() => setFilterCategory("violation")}
                className={cn(
                  "px-2.5 py-1 rounded-lg font-bold text-[11px] transition-all",
                  filterCategory === "violation"
                    ? "bg-rose-500 text-white"
                    : "bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400"
                )}
              >
                Violations (2)
              </button>
              <button
                onClick={() => setFilterCategory("warning")}
                className={cn(
                  "px-2.5 py-1 rounded-lg font-bold text-[11px] transition-all",
                  filterCategory === "warning"
                    ? "bg-amber-500 text-white"
                    : "bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400"
                )}
              >
                Warnings (3)
              </button>
              <button
                onClick={() => setFilterCategory("passed")}
                className={cn(
                  "px-2.5 py-1 rounded-lg font-bold text-[11px] transition-all",
                  filterCategory === "passed"
                    ? "bg-emerald-500 text-white"
                    : "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400"
                )}
              >
                Passed (48)
              </button>
            </div>

            {/* Rule List Rows */}
            <div className="space-y-1.5 max-h-[300px] overflow-y-auto pr-1">
              {filteredRules.map((rule) => {
                const isSelected = selectedRuleId === rule.id;
                return (
                  <button
                    key={rule.id}
                    onClick={() => setSelectedRuleId(rule.id)}
                    className={cn(
                      "w-full text-left p-2.5 rounded-xl border transition-all flex items-center justify-between text-xs",
                      isSelected
                        ? "bg-orange-50/80 dark:bg-orange-950/40 border-orange-500/60 shadow-2xs"
                        : "bg-slate-50 dark:bg-navy-950/60 border-slate-200/80 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700"
                    )}
                  >
                    <div className="flex items-center gap-2 min-w-0 pr-2">
                      {rule.status === "violation" ? (
                        <XCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />
                      ) : rule.status === "warning" ? (
                        <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0" />
                      ) : (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                      )}
                      <div className="min-w-0">
                        <p className="font-bold text-navy-900 dark:text-white truncate text-[11.5px]">
                          {t(rule.title, rule.titleUrdu)}
                        </p>
                        <p className="text-[10px] text-slate-400 truncate">
                          {rule.referenceCode} · {rule.locationGrid}
                        </p>
                      </div>
                    </div>

                    <div className="text-right flex-shrink-0">
                      <span
                        className={cn(
                          "px-1.5 py-0.5 rounded text-[9px] font-black uppercase tracking-wider",
                          rule.status === "violation"
                            ? "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                            : rule.status === "warning"
                            ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                            : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                        )}
                      >
                        {rule.status}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
