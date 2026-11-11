"use client";

import { useState, useEffect } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  MapPin,
  ArrowRight,
  ShieldCheck,
  Building2,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import { costService, CanonicalRateSnapshot } from "@/services/costService";

const cities = [
  { key: "lahore", labelEn: "Lahore", labelUr: "لاہور", apiName: "Lahore" },
  { key: "karachi", labelEn: "Karachi", labelUr: "کراچی", apiName: "Karachi" },
  { key: "islamabad", labelEn: "Islamabad", labelUr: "اسلام آباد", apiName: "Islamabad" },
] as const;

export default function MaterialRatesSection() {
  const { t } = useLanguage();
  const [selectedCity, setSelectedCity] = useState<"lahore" | "karachi" | "islamabad">("lahore");
  const [snapshots, setSnapshots] = useState<CanonicalRateSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [isLiveEngine, setIsLiveEngine] = useState(false);

  const fetchRates = async (cityKey: "lahore" | "karachi" | "islamabad") => {
    setLoading(true);
    const cityConfig = cities.find((c) => c.key === cityKey);
    const cityName = cityConfig ? cityConfig.apiName : "Lahore";

    try {
      const data = await costService.getSnapshots(cityName);
      if (data && data.length > 0) {
        setSnapshots(data);
        setIsLiveEngine(true);
      } else {
        setSnapshots([]);
        setIsLiveEngine(false);
      }
    } catch {
      setSnapshots([]);
      setIsLiveEngine(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRates(selectedCity);
  }, [selectedCity]);

  const handleRefresh = () => {
    fetchRates(selectedCity);
  };

  return (
    <section
      id="rates"
      className="py-24 bg-slate-50/70 dark:bg-navy-950/70 border-t border-slate-200/60 dark:border-slate-800"
    >
      <div className="container-custom">
        {/* Top Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-green-50 dark:bg-green-950/60 border border-green-200 dark:border-green-800/80 rounded-full mb-3">
              <span className={`w-2 h-2 rounded-full ${isLiveEngine ? "bg-emerald-500 animate-ping" : "bg-amber-500"}`} />
              <span className="text-xs font-bold text-green-700 dark:text-green-400 uppercase tracking-wider">
                {isLiveEngine
                  ? t("Canonical Market Rate Engine • PostgreSQL 17 Active", "مستند لائیو ریٹ انجن • ڈیٹا بیس منسلک")
                  : t("Connecting to Market Rate Engine...", "مارکیٹ ریٹ انجن سے رابطہ جاری ہے...")}
              </span>
            </div>
            <h2 className="section-title">
              {t("Live Material Rates Intelligence", "لائیو تعمیراتی میٹریل ریٹس")}
            </h2>
            <p className="section-subtitle mt-2">
              {t(
                "Multi-source weighted statistical composite and commercial market rates across Pakistan's major centers.",
                "پاکستان کے اہم مراکز میں سٹیل، سیمنٹ، ریت اور اینٹوں کی تصدیق شدہ مارکیٹ قیمتیں اور شماریاتی رجحانات۔"
              )}
            </p>
          </div>

          {/* City switcher & Refresh */}
          <div className="flex items-center gap-2.5 bg-white dark:bg-navy-900 p-1.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm self-start md:self-auto">
            <div className="flex items-center gap-1">
              {cities.map((city) => (
                <button
                  key={city.key}
                  onClick={() => setSelectedCity(city.key)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    selectedCity === city.key
                      ? "bg-orange-500 text-white shadow-sm"
                      : "text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  {t(city.labelEn, city.labelUr)}
                </button>
              ))}
            </div>

            <div className="w-px h-5 bg-slate-200 dark:bg-slate-700" />

            <button
              onClick={handleRefresh}
              aria-label="Refresh rates"
              className="p-1.5 text-slate-500 hover:text-orange-500 transition-colors"
              title={t("Refresh market feeds", "تازہ ترین ریٹس حاصل کریں")}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-orange-500" : ""}`} />
            </button>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="grid md:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div
                key={i}
                className="bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 animate-pulse h-64"
              >
                <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-24 mb-4" />
                <div className="h-6 bg-slate-200 dark:bg-slate-800 rounded w-48 mb-2" />
                <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-32 mb-6" />
                <div className="h-10 bg-slate-200 dark:bg-slate-800 rounded w-36 mb-4" />
                <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-full mt-auto" />
              </div>
            ))}
          </div>
        )}

        {/* Empty / Offline State */}
        {!loading && snapshots.length === 0 && (
          <div className="bg-white dark:bg-navy-900 rounded-2xl p-12 border border-slate-200 dark:border-slate-800 text-center max-w-xl mx-auto shadow-sm">
            <AlertCircle className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <h3 className="text-base font-bold text-navy-900 dark:text-white mb-2">
              {t("Market Rate Feed Offline", "مارکیٹ ریٹ فیڈ آف لائن ہے")}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-6">
              {t(
                "Unable to retrieve authentic canonical rate snapshots for this city. Please verify backend database connectivity.",
                "اس شہر کے لیے تصدیق شدہ مارکیٹ ریٹس دستیاب نہیں ہیں۔ براہ کرم سرور کنکشن چیک کریں۔"
              )}
            </p>
            <button
              onClick={handleRefresh}
              className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-xl text-xs font-bold transition-all"
            >
              {t("Retry Connection", "دوبارہ کوشش کریں")}
            </button>
          </div>
        )}

        {/* Dynamic Genuine Material Cards from DB */}
        {!loading && snapshots.length > 0 && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {snapshots.map((item) => {
              const isUp = item.trend === "up";
              const isDown = item.trend === "down";
              const unitFormatted = item.unit.replace(/_/g, " ");

              // Determine price basis note
              const isPbsBasis = item.product_name.toLowerCase().includes("bricks") ||
                item.product_name.toLowerCase().includes("sand") ||
                item.product_name.toLowerCase().includes("crush");

              return (
                <div
                  key={item.product_code}
                  className="group relative bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200/90 dark:border-slate-800 shadow-sm hover:shadow-xl hover:border-orange-500/40 transition-all duration-300 flex flex-col justify-between"
                >
                  <div>
                    {/* Header Badges */}
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-[11px] font-black uppercase tracking-widest px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        {item.category.toUpperCase()}
                      </span>
                      <div
                        className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold ${
                          isUp
                            ? "bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-900/50"
                            : isDown
                            ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/50"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                        }`}
                      >
                        {isUp ? (
                          <TrendingUp className="w-3.5 h-3.5" />
                        ) : isDown ? (
                          <TrendingDown className="w-3.5 h-3.5" />
                        ) : null}
                        <span>{item.confidence_score}% {t("Conf.", "اعتماد")}</span>
                      </div>
                    </div>

                    {/* Material Title & Spec */}
                    <h3 className="text-base font-bold text-navy-900 dark:text-white mb-1 group-hover:text-orange-500 transition-colors">
                      {item.product_name}
                    </h3>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 mb-4 font-mono">
                      {item.product_code}
                    </p>

                    {/* Big Price Tag */}
                    <div className="mb-4">
                      <div className="flex items-baseline gap-1.5">
                        <span className="text-xs font-bold text-slate-400 dark:text-slate-500">PKR</span>
                        <span className="text-3xl font-black tracking-tight text-navy-900 dark:text-white">
                          {Number(item.rate_pkr).toLocaleString("en-PK", {
                            minimumFractionDigits: 1,
                            maximumFractionDigits: 1,
                          })}
                        </span>
                      </div>
                      <span className="text-xs text-slate-500 dark:text-slate-400 mt-1 block">
                        per {unitFormatted} ·{" "}
                        <span className="capitalize font-semibold text-slate-700 dark:text-slate-300">
                          {item.city} Mandi
                        </span>
                      </span>

                      {item.price_range && item.price_range.min > 0 && (
                        <span className="text-[11px] text-slate-400 mt-1 block font-mono">
                          Spread: PKR {Number(item.price_range.min).toLocaleString("en-PK")} – {Number(item.price_range.max).toLocaleString("en-PK")}
                        </span>
                      )}
                    </div>

                    {/* Price Basis Classification Badge */}
                    <div className="mb-4">
                      <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                        isPbsBasis
                          ? "bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800"
                          : "bg-purple-50 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800"
                      }`}>
                        {isPbsBasis
                          ? t("PBS Statistical Retail Benchmark", "پی بی ایس شماریاتی ریٹیل بینچ مارک")
                          : t("Commercial Wholesale Market Quote", "تجارتی ہول سیل مارکیٹ ریٹ")}
                      </span>
                    </div>
                  </div>

                  {/* Bottom Status bar */}
                  <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
                      <MapPin className="w-3.5 h-3.5 text-orange-500" />
                      <span className="capitalize">{item.city}</span>
                      <span className="text-[10px] text-slate-400 font-mono">({item.observation_count} obs.)</span>
                    </div>
                    <div className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-semibold text-[11px]">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>{item.verification_status}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Action Link to Cost Dashboard */}
        <div className="mt-12 text-center">
          <Link
            href="/dashboard/costs"
            className="inline-flex items-center gap-2 text-sm font-semibold text-orange-500 hover:text-orange-600 transition-colors"
          >
            <span>{t("Explore Full Cost Intelligence Dashboard", "مکمل لاگت انٹیلی جنس ڈیش بورڈ دیکھیں")}</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}
