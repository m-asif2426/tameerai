"use client";

import { useState } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import { TrendingUp, TrendingDown, RefreshCw, MapPin, ArrowRight, ShieldCheck } from "lucide-react";
import Link from "next/link";

interface RateItem {
  id: string;
  key: "steel" | "cement" | "bricks";
  name: string;
  nameUrdu: string;
  spec: string;
  specUrdu: string;
  unit: string;
  unitUrdu: string;
  lahore: number;
  karachi: number;
  islamabad: number;
  change: number;
  trend: "up" | "down";
  benchmark: string;
}

const primaryRates: RateItem[] = [
  {
    id: "MAT-STEEL",
    key: "steel",
    name: "Deformed Steel Bars",
    nameUrdu: "سٹیل سریا (Grade 60)",
    spec: "ASTM A615 Grade 60 (Mughal / Amreli / FF)",
    specUrdu: "گریڈ 60 ہائی سٹرینتھ سریا",
    unit: "per Metric Ton",
    unitUrdu: "فی میٹرک ٹن",
    lahore: 285000,
    karachi: 282000,
    islamabad: 288000,
    change: +1.8,
    trend: "up",
    benchmark: "PKR 285k/ton",
  },
  {
    id: "MAT-CEMENT",
    key: "cement",
    name: "Portland Cement",
    nameUrdu: "پورٹ لینڈ سیمنٹ (OPC 53)",
    spec: "OPC 53 Grade (Lucky / Bestway / Maple Leaf)",
    specUrdu: "53 گریڈ معیاری او پی سی سیمنٹ",
    unit: "per 50kg Bag",
    unitUrdu: "فی 50 کلو بوری",
    lahore: 1150,
    karachi: 1120,
    islamabad: 1165,
    change: -1.2,
    trend: "down",
    benchmark: "PKR 1,150/bag",
  },
  {
    id: "MAT-BRICKS",
    key: "bricks",
    name: "Red Kiln Bricks",
    nameUrdu: "اول درجہ سرخ اینٹیں (Awal Bricks)",
    spec: "A-Quality Baked Clay, 9\" x 4.5\" x 3\"",
    specUrdu: "پختہ پکی ہوئی اول کوالٹی سرخ اینٹیں",
    unit: "per 1,000 Pcs",
    unitUrdu: "فی 1000 عدد",
    lahore: 18500,
    karachi: 19200,
    islamabad: 19800,
    change: +0.6,
    trend: "up",
    benchmark: "PKR 18.5k/1k",
  },
];

export default function MaterialRatesSection() {
  const { t } = useLanguage();
  const [selectedCity, setSelectedCity] = useState<"lahore" | "karachi" | "islamabad">("lahore");
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 600);
  };

  const cities = [
    { key: "lahore", labelEn: "Lahore", labelUr: "لاہور" },
    { key: "karachi", labelEn: "Karachi", labelUr: "کراچی" },
    { key: "islamabad", labelEn: "Islamabad", labelUr: "اسلام آباد" },
  ] as const;

  return (
    <section className="py-24 bg-slate-50/70 dark:bg-navy-950/70 border-t border-slate-200/60 dark:border-slate-800">
      <div className="container-custom">
        {/* Top Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-green-50 dark:bg-green-950/60 border border-green-200 dark:border-green-800/80 rounded-full mb-3">
              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-ping" />
              <span className="text-xs font-bold text-green-700 dark:text-green-400 uppercase tracking-wider">
                {t("Real-Time Cost Intelligence", "ریئل ٹائم تعمیراتی لاگت انٹیلی جنس")}
              </span>
            </div>
            <h2 className="section-title">
              {t("Live Material Rates Preview", "لائیو تعمیراتی میٹریل ریٹس")}
            </h2>
            <p className="section-subtitle mt-2">
              {t(
                "Spotlight prices for Steel, Cement, and Bricks across Pakistan's major metropolitan markets.",
                "پاکستان کے اہم شہروں میں سٹیل، سیمنٹ اور اینٹوں کی موجودہ مارکیٹ قیمتیں اور رجحانات۔"
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
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin text-orange-500" : ""}`} />
            </button>
          </div>
        </div>

        {/* 3 Core Cards: Steel, Cement, Bricks */}
        <div className="grid md:grid-cols-3 gap-6">
          {primaryRates.map((item) => {
            const price = item[selectedCity];
            const isUp = item.trend === "up";

            return (
              <div
                key={item.id}
                className="group relative bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200/90 dark:border-slate-800 shadow-sm hover:shadow-xl hover:border-orange-500/40 transition-all duration-300"
              >
                {/* Header Badge */}
                <div className="flex items-center justify-between mb-4">
                  <span className="text-[11px] font-black uppercase tracking-widest px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                    {item.key.toUpperCase()}
                  </span>
                  <div
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold ${
                      isUp
                        ? "bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-900/50"
                        : "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/50"
                    }`}
                  >
                    {isUp ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                    <span>
                      {isUp ? "+" : ""}
                      {item.change}% {t("this week", "اس ہفتے")}
                    </span>
                  </div>
                </div>

                {/* Material Title & Spec */}
                <h3 className="text-lg font-bold text-navy-900 dark:text-white mb-1 group-hover:text-orange-500 transition-colors">
                  {t(item.name, item.nameUrdu)}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-6 line-clamp-1">
                  {t(item.spec, item.specUrdu)}
                </p>

                {/* Big Price Tag */}
                <div className="mb-6">
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-xs font-bold text-slate-400 dark:text-slate-500">PKR</span>
                    <span className="text-3xl font-black tracking-tight text-navy-900 dark:text-white">
                      {price.toLocaleString()}
                    </span>
                  </div>
                  <span className="text-xs text-slate-500 dark:text-slate-400 mt-1 block">
                    {t(item.unit, item.unitUrdu)} ·{" "}
                    <span className="capitalize font-semibold text-slate-700 dark:text-slate-300">
                      {selectedCity} {t("Mandi", "منڈی")}
                    </span>
                  </span>
                </div>

                {/* Bottom Status bar */}
                <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
                    <MapPin className="w-3.5 h-3.5 text-orange-500" />
                    <span className="capitalize">{selectedCity}</span>
                  </div>
                  <div className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-semibold">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>{t("Verified Daily", "روزانہ تصدیق شدہ")}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Action Link to Cost Dashboard */}
        <div className="mt-12 text-center">
          <Link
            href="/dashboard/costs"
            className="inline-flex items-center gap-2 text-sm font-bold text-orange-600 dark:text-orange-400 hover:text-orange-700 dark:hover:text-orange-300 transition-colors group"
          >
            <span>{t("View full BOQ price trends and forecasting in Cost Intelligence", "لاگت انٹیلی جنس میں مکمل بی او کیو رجحانات اور پیشن گوئی دیکھیں")}</span>
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </Link>
        </div>
      </div>
    </section>
  );
}
