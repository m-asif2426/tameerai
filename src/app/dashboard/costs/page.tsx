"use client";

import { useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Coins,
  DollarSign,
  BarChart3,
  Calendar,
  Building2,
  RefreshCw,
  Download,
  Bot,
  Filter,
  CheckCircle2,
  Info,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  Sparkles,
  Calculator,
  ShieldAlert,
  SlidersHorizontal,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  Legend,
} from "recharts";
import { cn } from "@/lib/utils";

// --- Monthly Material Price Trend Data ---
const PRICE_TRENDS_DATA = [
  { month: "May", steel: 232000, cement: 1350, bricks: 13800 },
  { month: "Jun", steel: 235000, cement: 1370, bricks: 14000 },
  { month: "Jul", steel: 238000, cement: 1390, bricks: 14200 },
  { month: "Aug", steel: 242000, cement: 1410, bricks: 14400 },
  { month: "Sep", steel: 245000, cement: 1430, bricks: 14500 },
  { month: "Oct (Now)", steel: 248500, cement: 1420, bricks: 14500 },
  { month: "Nov (AI)", steel: 251000, cement: 1435, bricks: 14600 },
  { month: "Dec (AI)", steel: 254000, cement: 1450, bricks: 14750 },
];

// --- Budget Comparison Data by Milestone/Phase ---
const BUDGET_COMPARISON_DATA = [
  { phase: "Foundation & Raft", budget: 28.5, estimated: 29.2, overrun: 0.7 },
  { phase: "RCC Superstructure", budget: 45.0, estimated: 49.8, overrun: 4.8 },
  { phase: "Brick Masonry", budget: 14.5, estimated: 15.2, overrun: 0.7 },
  { phase: "Plumbing & Electrical", budget: 16.0, estimated: 17.1, overrun: 1.1 },
  { phase: "Finishing & Façade", budget: 16.0, estimated: 17.15, overrun: 1.15 },
];

export default function CostIntelligencePage() {
  const { t, language } = useLanguage();

  // Active City for Live Rates
  const [selectedCity, setSelectedCity] = useState<"Lahore" | "Karachi" | "Islamabad">("Lahore");
  const [activeProject, setActiveProject] = useState("PRJ-001");
  const [chartMetric, setChartMetric] = useState<"steel" | "cement" | "all">("all");

  // Core Financial Figures for DHA Commercial Plaza
  const projectBudget = 120000000; // 12 Crore PKR (PKR 120,000,000)
  const estimatedCost = 128450000; // 12.845 Crore PKR (Overrun: +PKR 8.45M)
  const costVariance = estimatedCost - projectBudget;
  const variancePercentage = "+7.04%";

  // Material Cards Data
  const materialCards = [
    {
      id: "steel",
      name: "Steel (Deformed Gr.60)",
      nameUrdu: "اسٹیل (ڈیفارمڈ گریڈ 60)",
      spec: "ASTM A615 / BS 4449 (60,000 psi)",
      unit: "per Ton",
      unitUrdu: "فی ٹن",
      currentPrice: selectedCity === "Karachi" ? "PKR 252,000" : selectedCity === "Islamabad" ? "PKR 250,000" : "PKR 248,500",
      boqBaseRate: "PKR 236,000",
      variance: "+5.3%",
      trend: "up" as const,
      quantityRequired: "340 Tons",
      estimatedImpact: "+PKR 4,250,000 Overrun",
      primaryBrands: "Mughal, Ittefaq, Amreli",
      riskLevel: "high" as const,
    },
    {
      id: "cement",
      name: "Cement (OPC 50kg Bag)",
      nameUrdu: "سیمنٹ (او پی سی 50 کلو بوری)",
      spec: "ASTM C150 / PS 232 Type-1",
      unit: "per Bag",
      unitUrdu: "فی بوری",
      currentPrice: selectedCity === "Karachi" ? "PKR 1,450" : selectedCity === "Islamabad" ? "PKR 1,410" : "PKR 1,420",
      boqBaseRate: "PKR 1,380",
      variance: "+2.9%",
      trend: "down" as const,
      quantityRequired: "28,500 Bags",
      estimatedImpact: "+PKR 1,140,000 Overrun",
      primaryBrands: "Bestway, Lucky, Maple Leaf",
      riskLevel: "medium" as const,
    },
    {
      id: "bricks",
      name: "Bricks (Awwal Red Clay)",
      nameUrdu: "اول سرخ اینٹیں (Bricks)",
      spec: "Standard Kiln Baked Grade A+",
      unit: "per 1,000 pcs",
      unitUrdu: "فی ہزار",
      currentPrice: selectedCity === "Karachi" ? "PKR 15,200" : selectedCity === "Islamabad" ? "PKR 14,800" : "PKR 14,500",
      boqBaseRate: "PKR 14,000",
      variance: "+3.6%",
      trend: "stable" as const,
      quantityRequired: "140,000 Pieces",
      estimatedImpact: "+PKR 650,000 Overrun",
      primaryBrands: "Bhatta Kiln A+",
      riskLevel: "low" as const,
    },
  ];

  return (
    <div className="space-y-6 pb-12 font-sans">
      {/* ========================================================================= */}
      {/* TOP HEADER & PROJECT SELECTION                                            */}
      {/* ========================================================================= */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20">
              {t("Financial Cost Intelligence", "مالیاتی لاگت انٹیلی جنس")}
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {t("BOQ Variance & Live Commodity Index", "بی او کیو اور لائیو مارکیٹ ریٹس")}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white tracking-tight flex items-center gap-2.5">
            <Coins className="w-6 h-6 text-orange-500" />
            <span>{t("Cost Intelligence", "لاگت انٹیلی جنس (Cost Intelligence)")}</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {t(
              "Predictive budget forecasting, material rate inflation tracking, and cost overrun mitigation for Pakistani construction.",
              "بجٹ کی پیشن گوئی، مٹیریل کی قیمتوں میں افراط زر کی ٹریکنگ اور لاگت کا تجزیہ۔"
            )}
          </p>
        </div>

        {/* City and Actions Bar */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* City Toggle */}
          <div className="flex bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 p-0.5 rounded-xl text-xs font-bold shadow-2xs">
            {(["Lahore", "Karachi", "Islamabad"] as const).map((city) => (
              <button
                key={city}
                onClick={() => setSelectedCity(city)}
                className={cn(
                  "px-3 py-1.5 rounded-lg transition-all",
                  selectedCity === city
                    ? "bg-orange-500 text-white shadow-2xs font-bold"
                    : "text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white"
                )}
              >
                {t(city, city === "Lahore" ? "لاہور" : city === "Karachi" ? "کراچی" : "اسلام آباد")}
              </button>
            ))}
          </div>

          <Link
            href="/dashboard/ai-assistant"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-navy-900 dark:bg-navy-800 hover:bg-navy-800 text-white transition-all shadow-2xs"
          >
            <Bot className="w-3.5 h-3.5 text-orange-400" />
            <span>{t("Cost AI Forecast", "اے آئی لاگت مشورہ")}</span>
          </Link>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TOP SECTION: PROJECT BUDGET + ESTIMATED COST + COST RISK & RISK INDICATOR */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Card 1: PROJECT BUDGET */}
        <div className="p-5 sm:p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {t("Project Budget", "منظور شدہ بجٹ (Project Budget)")}
            </span>
            <div className="w-9 h-9 rounded-xl bg-slate-100 dark:bg-navy-950 text-slate-600 dark:text-slate-400 flex items-center justify-center">
              <DollarSign className="w-5 h-5" />
            </div>
          </div>

          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white font-mono tracking-tight">
                PKR 120.0M
              </span>
              <span className="text-xs font-bold text-slate-400">
                (12 {t("Crore", "کروڑ")})
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              {t("Approved baseline capital for DHA Commercial Plaza", "ڈی ایچ اے کمرشل پلازہ کا کل مختص بجٹ")}
            </p>
          </div>

          <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
            <span>{t("Disbursed to Date:", "اب تک خرچ:")} <strong>PKR 38.4M (32%)</strong></span>
            <span className="text-emerald-600 font-bold">On Schedule</span>
          </div>
        </div>

        {/* Card 2: ESTIMATED COST */}
        <div className="p-5 sm:p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {t("Estimated Cost", "تخمینہ شدہ حتمی لاگت (Estimated Cost)")}
            </span>
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 flex items-center justify-center">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>

          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white font-mono tracking-tight">
                PKR 128.45M
              </span>
              <span className="text-xs font-black text-rose-600 dark:text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20">
                {variancePercentage}
              </span>
            </div>
            <p className="text-xs text-rose-600 dark:text-rose-400 mt-1 font-semibold flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>+PKR 8,450,000 {t("Forecasted Cost Overrun", "لاگت میں متوقع اضافہ")}</span>
            </p>
          </div>

          <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
            <span>{t("Variance Driver:", "بنیادی وجہ:")} <strong className="text-navy-900 dark:text-white">{t("Steel Gr.60 Inflation", "اسٹیل ریٹس")}</strong></span>
            <span className="text-rose-500 font-bold">+5.3%</span>
          </div>
        </div>

        {/* Card 3: COST RISK & RISK INDICATOR (Low, Medium, High) */}
        <div className="p-5 sm:p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {t("Cost Risk Exposure", "لاگت کا مجموعی خطرہ (Cost Risk)")}
            </span>
            <div className="w-9 h-9 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 flex items-center justify-center">
              <ShieldAlert className="w-5 h-5" />
            </div>
          </div>

          <div>
            {/* THREE-STAGE RISK INDICATOR: LOW, MEDIUM, HIGH */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
                  {t("Risk Indicator:", "رسک انڈیکیٹر:")}
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-black uppercase bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                  {t("Medium Risk (7.0% Overrun)", "درمیانہ خطرہ (Medium)")}
                </span>
              </div>

              {/* Segmented Meter Bar: Low | Medium | High */}
              <div className="grid grid-cols-3 gap-1.5 h-3">
                {/* Low Segment */}
                <div
                  className="rounded-l-full bg-emerald-500 transition-all opacity-80"
                  title="Low Risk (0-3% variance)"
                />
                {/* Medium Segment (ACTIVE) */}
                <div
                  className="bg-amber-500 ring-2 ring-amber-500/50 relative shadow-sm"
                  title="Medium Risk (3-8% variance) - ACTIVE"
                >
                  <span className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full bg-white ring-2 ring-amber-600" />
                </div>
                {/* High Segment */}
                <div
                  className="rounded-r-full bg-slate-200 dark:bg-navy-800 transition-all opacity-40"
                  title="High Risk (>8% variance)"
                />
              </div>

              <div className="flex justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                <span className="text-emerald-600">{t("Low (0-3%)", "کم خطرہ")}</span>
                <span className="text-amber-600 font-extrabold">{t("Medium (3-8%)", "درمیانہ خطرہ")}</span>
                <span className="text-slate-400">{t("High (>8%)", "زیادہ خطرہ")}</span>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
            <span>{t("Mitigation:", "حل:")} <strong>{t("Advance Bulk Rebar Lock", "اسٹیل کی پیشگی خریداری")}</strong></span>
            <span className="text-orange-500 hover:underline font-bold cursor-pointer">
              {t("Apply Buffer →", "تدبیر دیکھیں →")}
            </span>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* MATERIAL CARDS: STEEL, CEMENT, BRICKS                                     */}
      {/* ========================================================================= */}
      <div>
        <div className="flex items-center justify-between mb-3.5">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-navy-900 dark:text-white uppercase tracking-wider">
              {t("Core Construction Material Indices", "بنیادی تعمیراتی میٹریل ریٹس")}
            </h2>
            <span className="text-xs text-slate-400">({selectedCity})</span>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {t("Updated today · Pakistan Steel & Cement Index", "آج تصدیق شدہ")}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {materialCards.map((mat) => (
            <div
              key={mat.id}
              className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-4 hover:border-orange-500/40 transition-all"
            >
              {/* Card Header: Material Title & Trend */}
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    {mat.spec}
                  </span>
                  <h3 className="text-base font-black text-navy-900 dark:text-white mt-0.5">
                    {t(mat.name, mat.nameUrdu)}
                  </h3>
                </div>

                <span
                  className={cn(
                    "inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-black font-mono",
                    mat.trend === "up"
                      ? "bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20"
                      : mat.trend === "down"
                      ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                      : "bg-slate-100 dark:bg-navy-950 text-slate-600 dark:text-slate-400"
                  )}
                >
                  {mat.trend === "up" && <TrendingUp className="w-3.5 h-3.5" />}
                  {mat.trend === "down" && <TrendingDown className="w-3.5 h-3.5" />}
                  {mat.variance}
                </span>
              </div>

              {/* Price Details Grid */}
              <div className="grid grid-cols-2 gap-2 p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800/80 text-xs">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">
                    {t("Current Market Rate", "موجودہ ریٹ")}
                  </span>
                  <p className="text-sm font-black text-navy-900 dark:text-white font-mono mt-0.5">
                    {mat.currentPrice}
                  </p>
                  <span className="text-[10px] text-slate-400">{t(mat.unit, mat.unitUrdu)}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">
                    {t("BOQ Baseline Rate", "بی او کیو ریٹ")}
                  </span>
                  <p className="text-sm font-bold text-slate-500 dark:text-slate-400 font-mono mt-0.5">
                    {mat.boqBaseRate}
                  </p>
                  <span className="text-[10px] text-slate-400">{t(mat.unit, mat.unitUrdu)}</span>
                </div>
              </div>

              {/* Quantity Required & Financial Overrun Impact */}
              <div className="space-y-1.5 text-xs">
                <div className="flex items-center justify-between text-slate-600 dark:text-slate-300">
                  <span>{t("Total BOQ Quantity:", "مطلوبہ مقدار:")}</span>
                  <strong className="text-navy-900 dark:text-white font-mono">{mat.quantityRequired}</strong>
                </div>
                <div className="flex items-center justify-between text-slate-600 dark:text-slate-300">
                  <span>{t("Project Cost Impact:", "لاگت پر اثر:")}</span>
                  <strong className="text-rose-600 dark:text-rose-400 font-bold">{mat.estimatedImpact}</strong>
                </div>
              </div>

              {/* Footer: Verified Brands */}
              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                <span>{t("Brands:", "برانڈز:")} <strong className="text-slate-600 dark:text-slate-300">{mat.primaryBrands}</strong></span>
                <span className="text-orange-500 font-semibold cursor-pointer hover:underline">
                  {t("Suppliers →", "سپلائرز →")}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* CHARTS: 1. PRICE TRENDS   2. BUDGET COMPARISON BY PHASE                   */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* CHART 1: PRICE TRENDS (Area Chart) */}
        <div className="lg:col-span-7 p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-bold text-navy-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-orange-500" />
                <span>{t("Material Price Trends & AI Forecast", "قیمتوں کے رجحانات اور اے آئی پیشگوئی")}</span>
              </h3>
              <p className="text-xs text-slate-400">
                {t("6-Month Historical + 2-Month AI Neural Forward Projection (Steel Gr.60 in PKR / Ton)", "اسٹیل گریڈ 60 کے ماہانہ ریٹس")}
              </p>
            </div>

            <div className="flex items-center gap-1.5 text-xs font-semibold">
              <span className="px-2 py-0.5 rounded-md bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 text-[10px]">
                Steel Gr.60 (PKR/Ton)
              </span>
            </div>
          </div>

          {/* Area Chart Container */}
          <div className="w-full h-64 sm:h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={PRICE_TRENDS_DATA} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="steelGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.15} />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 11, fill: "#94a3b8" }}
                  axisLine={{ stroke: "#cbd5e1" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: "#94a3b8" }}
                  axisLine={false}
                  tickLine={false}
                  domain={[220000, 260000]}
                  tickFormatter={(val) => `${(val / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  formatter={(value?: number | string | readonly (number | string)[]) => [`PKR ${(Number(value || 0)).toLocaleString()}`, "Steel Gr.60 / Ton"]}
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#334155",
                    borderRadius: "12px",
                    color: "#f8fafc",
                    fontSize: "12px",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="steel"
                  stroke="#f97316"
                  strokeWidth={3}
                  fill="url(#steelGradient)"
                  dot={{ r: 4, fill: "#f97316", strokeWidth: 2, stroke: "#ffffff" }}
                  activeDot={{ r: 6, fill: "#ea580c" }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-orange-500" />
              <span>{t("Steel Price Trend (Historical + Forecast)", "اسٹیل کے ریٹس کا رجحان")}</span>
            </span>
            <span className="text-[11px] font-mono text-slate-500">
              {t("Source: Pakistan Steel Melters Association (PSMA)", "ماخذ: پاکستان اسٹیل میلٹرز ایسوسی ایشن")}
            </span>
          </div>
        </div>

        {/* CHART 2: BUDGET COMPARISON BY PHASE (Grouped Bar Chart) */}
        <div className="lg:col-span-5 p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-navy-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-emerald-500" />
                <span>{t("Budget Comparison", "بجٹ بمقابلہ اصل تخمینہ (Budget Comparison)")}</span>
              </h3>
              <p className="text-xs text-slate-400">
                {t("Allocated Budget vs Forecasted Spend (Millions PKR)", "مختلف مراحل میں بجٹ کا موازنہ (ملین روپے)")}
              </p>
            </div>
          </div>

          {/* Bar Chart Container */}
          <div className="w-full h-64 sm:h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={BUDGET_COMPARISON_DATA}
                margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.15} />
                <XAxis
                  dataKey="phase"
                  tick={{ fontSize: 9, fill: "#94a3b8" }}
                  axisLine={{ stroke: "#cbd5e1" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: "#94a3b8" }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(val) => `${val}M`}
                />
                <Tooltip
                  formatter={(value?: number | string | readonly (number | string)[], name?: string | number) => [
                    `PKR ${Number(value || 0).toFixed(1)} Million`,
                    name === "budget" ? "Allocated Budget" : "Estimated Cost",
                  ]}
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#334155",
                    borderRadius: "12px",
                    color: "#f8fafc",
                    fontSize: "12px",
                  }}
                />
                <Legend
                  wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
                  formatter={(value) => (value === "budget" ? "Allocated Budget" : "Estimated Cost")}
                />
                <Bar dataKey="budget" fill="#94a3b8" radius={[4, 4, 0, 0]} name="budget" />
                <Bar dataKey="estimated" fill="#f97316" radius={[4, 4, 0, 0]} name="estimated" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>{t("Highest Variance Phase:", "سب سے زیادہ فرق:")} <strong className="text-rose-500">RCC Superstructure (+PKR 4.8M)</strong></span>
            <Link href="/dashboard/ai-assistant" className="text-orange-500 hover:underline font-bold text-[11px]">
              {t("Ask AI to Optimize →", "لاگت کم کرنے کی تجاویز →")}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
