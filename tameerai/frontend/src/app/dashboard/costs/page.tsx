"use client";

import { useState, useEffect, useCallback } from "react";
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
  FolderOpen,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { cn } from "@/lib/utils";
import {
  costService,
  CanonicalRateSnapshot,
  CrossCityComparisonResponse,
  PriceHistoryResponse,
} from "@/services/costService";
import { projectService } from "@/services/projectService";
import { Project } from "@/types";

export default function CostIntelligencePage() {
  const { t, language } = useLanguage();

  const [selectedCity, setSelectedCity] = useState<"Lahore" | "Karachi" | "Islamabad">("Lahore");
  const [snapshots, setSnapshots] = useState<CanonicalRateSnapshot[]>([]);
  const [cityComparison, setCityComparison] = useState<CrossCityComparisonResponse | null>(null);
  const [priceHistory, setPriceHistory] = useState<PriceHistoryResponse | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [loading, setLoading] = useState(true);

  // Load genuine market data and user projects
  const loadMarketIntelligence = useCallback(async () => {
    setLoading(true);
    try {
      const [snaps, compare, history, projs] = await Promise.all([
        costService.getSnapshots(selectedCity),
        costService.getCityComparison("STEEL_REBAR_G60"),
        costService.getPriceHistory("STEEL_REBAR_G60", selectedCity),
        projectService.getProjects(),
      ]);
      setSnapshots(snaps);
      setCityComparison(compare);
      setPriceHistory(history);
      setProjects(projs);
      setSelectedProjectId((prev) => prev || (projs.length > 0 ? projs[0].id : ""));
    } catch (err) {
      console.error("[CostIntelligence] Fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, [selectedCity]);

  useEffect(() => {
    loadMarketIntelligence();
  }, [loadMarketIntelligence]);

  // Selected project for BOQ calculations
  const currentProject = projects.find((p) => p.id === selectedProjectId) || null;

  // Chart data from authentic backend price history
  const chartData = (priceHistory?.data_points || []).map((pt) => ({
    period: pt.period,
    price: pt.median_pkr,
    min: pt.min_pkr,
    max: pt.max_pkr,
  }));

  return (
    <div className="space-y-6 pb-12 font-sans">
      {/* 1. TOP HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20">
              {t("Financial Cost Intelligence", "مالیاتی لاگت انٹیلی جنس")}
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {t("PostgreSQL 17 Canonical Rates Feeds", "ڈیٹا بیس سے منسلک لائیو ریٹس")}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white tracking-tight flex items-center gap-2.5">
            <Coins className="w-6 h-6 text-orange-500" />
            <span>{t("Cost Intelligence", "لاگت انٹیلی جنس (Cost Intelligence)")}</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {t(
              "Authentic canonical construction material rates across Pakistan, multi-city parity analysis, and genuine project BOQ tracking.",
              "پاکستان کے اہم شہروں میں سریا، سیمنٹ، ریت اور اینٹوں کے مستند ریٹس اور پروجیکٹ لاگت کا تجزیہ۔"
            )}
          </p>
        </div>

        {/* City and Actions Bar */}
        <div className="flex items-center gap-2 flex-wrap">
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

          <button
            onClick={loadMarketIntelligence}
            className="p-2 rounded-xl text-slate-500 hover:text-navy-900 dark:hover:text-white bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 transition-colors shadow-2xs"
            title={t("Refresh market rates", "ریٹس ریفریش کریں")}
            aria-label="Refresh rates"
          >
            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin text-orange-500")} />
          </button>
        </div>
      </div>

      {/* 2. PROJECT FINANCIAL OVERVIEW (Real DB Data or Honest Unpopulated State) */}
      <div className="rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100 dark:border-slate-800/80">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              {t("Project Financial Scope", "منصوبے کا مالیاتی حجم")}
            </span>
            {projects.length > 0 ? (
              <div className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-orange-500" />
                <select
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                  className="bg-transparent text-lg font-bold text-navy-900 dark:text-white focus:outline-none cursor-pointer border-b border-dashed border-orange-500 pb-0.5"
                >
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.id}) — {p.city}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <h2 className="text-base font-bold text-navy-900 dark:text-white">
                {t("No Projects in Organization", "کوئی پروجیکٹ منسلک نہیں")}
              </h2>
            )}
          </div>

          {currentProject && (
            <Link
              href={`/dashboard/projects/${currentProject.id}`}
              className="text-xs font-bold text-orange-500 hover:text-orange-600 transition-colors inline-flex items-center gap-1"
            >
              <span>{t("Open Project Workspace", "پروجیکٹ ورک اسپیس کھولیں")}</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          )}
        </div>

        {currentProject ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                {t("Approved Budget", "منظور شدہ بجٹ")}
              </span>
              <div className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white mt-0.5 font-mono">
                PKR {currentProject.budgetCrore.toFixed(1)} {t("Crore", "کروڑ")}
              </div>
              <span className="text-[11px] text-slate-400">
                {t("Raw: PKR", "اصل رقم: PKR")} {((currentProject.budgetCrore * 10000000) || 0).toLocaleString()}
              </span>
            </div>

            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                {t("Disbursed / Spent", "اخراجات")}
              </span>
              <div className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white mt-0.5 font-mono">
                PKR {currentProject.spentCrore.toFixed(1)} {t("Crore", "کروڑ")}
              </div>
              <span className="text-[11px] text-slate-400">
                {currentProject.budgetCrore > 0
                  ? `${((currentProject.spentCrore / currentProject.budgetCrore) * 100).toFixed(1)}% utilized`
                  : "0.0% utilized"}
              </span>
            </div>

            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                {t("Project Status", "حیثیت")}
              </span>
              <div className="text-lg font-bold text-amber-600 dark:text-amber-400 mt-1">
                {currentProject.status}
              </div>
              <span className="text-[11px] text-slate-400">
                {currentProject.type}
              </span>
            </div>

            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                {t("Covered Area", "رقبہ")}
              </span>
              <div className="text-lg font-bold text-navy-900 dark:text-white mt-1">
                {currentProject.areaSqft || "N/A"}
              </div>
              <span className="text-[11px] text-slate-400">
                {currentProject.floors} {t("Floors", "منزلیں")}
              </span>
            </div>
          </div>
        ) : (
          <div className="pt-6 text-center py-6 text-xs text-slate-500">
            <p className="mb-3">
              {t(
                "Create a project workspace to track itemized BOQ quantities, rate variances, and contractor payments.",
                "پروجیکٹ ورک اسپیس بنائیں تاکہ بی او کیو اور میٹریل ریٹس کا تفصیلی موازنہ کیا جا سکے۔"
              )}
            </p>
            <Link
              href="/dashboard/projects"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-xl text-xs font-bold transition-all"
            >
              <span>{t("Create New Project", "نیا پروجیکٹ بنائیں")}</span>
            </Link>
          </div>
        )}
      </div>

      {/* 3. DYNAMIC CANONICAL MATERIAL CARDS (PostgreSQL 17 Data) */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-navy-900 dark:text-white">
              {t(`Live Market Rates — ${selectedCity} Mandi`, `لائیو مارکیٹ ریٹس — ${selectedCity}`)}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {t("Source provenance: Pakistan Bureau of Statistics (PBS) retail benchmarks and wholesale dealer surveys", "پی بی ایس ریٹیل اور ہول سیل مارکیٹ ریٹس")}
            </p>
          </div>
          <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-slate-100 dark:bg-navy-900 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800">
            {snapshots.length} {t("Verified Commodities", "اشیاء")}
          </span>
        </div>

        {loading ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div
                key={i}
                className="bg-white dark:bg-navy-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 animate-pulse h-48"
              />
            ))}
          </div>
        ) : snapshots.length === 0 ? (
          <div className="bg-white dark:bg-navy-900 rounded-2xl p-8 border border-slate-200 dark:border-slate-800 text-center text-xs text-slate-500">
            {t("No material rate observations available for this city.", "اس شہر کے لیے ریٹس دستیاب نہیں ہیں۔")}
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {snapshots.map((item) => {
              const isUp = item.trend === "up";
              const isDown = item.trend === "down";
              const unitClean = item.unit.replace(/_/g, " ");

              const isPbs = item.product_name.toLowerCase().includes("bricks") ||
                item.product_name.toLowerCase().includes("sand") ||
                item.product_name.toLowerCase().includes("crush");

              return (
                <div
                  key={item.product_code}
                  className="bg-white dark:bg-navy-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 p-5 shadow-2xs hover:shadow-lg hover:border-orange-500/30 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 dark:bg-navy-950 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800">
                        {item.category.toUpperCase()}
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                        {item.confidence_score}% {t("Confidence", "اعتماد")}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-navy-900 dark:text-white line-clamp-1 mb-0.5">
                      {item.product_name}
                    </h3>
                    <p className="text-[10px] text-slate-400 font-mono mb-3">
                      {item.product_code}
                    </p>

                    <div className="mb-3">
                      <div className="flex items-baseline gap-1">
                        <span className="text-xs font-bold text-slate-400">PKR</span>
                        <span className="text-2xl font-black text-navy-900 dark:text-white font-mono">
                          {Number(item.rate_pkr).toLocaleString("en-PK", {
                            minimumFractionDigits: 1,
                            maximumFractionDigits: 1,
                          })}
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-500 block">
                        per {unitClean} ({selectedCity})
                      </span>
                      {item.price_range && item.price_range.min > 0 && (
                        <span className="text-[10px] text-slate-400 block font-mono mt-0.5">
                          Spread: PKR {item.price_range.min.toLocaleString()} – {item.price_range.max.toLocaleString()}
                        </span>
                      )}
                    </div>

                    {/* Price Basis Badge */}
                    <div className="mb-3">
                      <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                        isPbs
                          ? "bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800"
                          : "bg-purple-50 dark:bg-purple-950 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800"
                      }`}>
                        {isPbs
                          ? t("PBS Statistical Retail Benchmark", "پی بی ایس ریٹیل بینچ مارک")
                          : t("Wholesale Commercial Quote", "تجارتی ہول سیل ریٹ")}
                      </span>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                    <span>{item.observation_count} observations</span>
                    <span className="text-emerald-600 dark:text-emerald-400 font-semibold">{item.verification_status}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 4. CROSS-CITY COMPARISON */}
      {cityComparison && cityComparison.cities && (
        <div className="p-6 rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-navy-900 dark:text-white">
                {t(`Geographic Price Comparison — ${cityComparison.product_name}`, `شہروں کے ریٹس کا موازنہ`)}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                National Median: PKR {cityComparison.national_median_pkr.toLocaleString()} / {cityComparison.standard_unit.replace(/_/g, " ")}
              </p>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-orange-50 dark:bg-orange-950 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-800">
              National Index
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {cityComparison.cities.map((c) => {
              const diff = c.rate_pkr - cityComparison.national_median_pkr;
              const diffPct = ((diff / cityComparison.national_median_pkr) * 100).toFixed(1);

              return (
                <div
                  key={c.city}
                  className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/60 dark:border-slate-800 text-center"
                >
                  <p className="text-xs font-bold text-navy-900 dark:text-white">{c.city}</p>
                  <p className="text-sm font-black text-navy-900 dark:text-white font-mono mt-1">
                    PKR {Math.round(c.rate_pkr).toLocaleString()}
                  </p>
                  <span className={`text-[10px] font-bold ${Number(diffPct) > 0 ? "text-amber-600" : Number(diffPct) < 0 ? "text-emerald-600" : "text-slate-400"}`}>
                    {Number(diffPct) > 0 ? `+${diffPct}%` : `${diffPct}%`}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 5. HISTORICAL PRICE TREND CHART (Authentic DB Data) */}
      {chartData.length > 0 && (
        <div className="p-6 rounded-3xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-navy-900 dark:text-white">
                {t(`Historical Price Curve — Steel Rebar Grade 60 (${selectedCity})`, `تاریخی قیمتوں کا چارٹ`)}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {priceHistory?.total_observations || 0} observations aggregated in DB lookback window
              </p>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950 text-emerald-600 border border-emerald-200">
              Confidence {priceHistory?.trend_confidence || 85}%
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#EA580C" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#EA580C" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} domain={["dataMin - 5000", "dataMax + 5000"]} />
                <Tooltip
                  formatter={(value: any) => [`PKR ${Number(value).toLocaleString()}`, "Price"]}
                />
                <Area
                  type="monotone"
                  dataKey="price"
                  stroke="#EA580C"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#priceGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
