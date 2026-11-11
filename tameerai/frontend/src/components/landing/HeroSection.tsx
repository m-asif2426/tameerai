"use client";

import { useLanguage } from "@/contexts/LanguageContext";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight,
  HardHat,
  ShieldCheck,
  TrendingUp,
  FileCheck2,
} from "lucide-react";

const floatingCards = [
  {
    icon: ShieldCheck,
    label: "PBC 2021 Compliant",
    labelUr: "پی بی سی 2021 باضابطہ",
    color: "text-green-600 dark:text-green-400",
    bg: "bg-green-50 dark:bg-green-900/30",
    position: "top-8 left-8",
  },
  {
    icon: TrendingUp,
    label: "Live Market Benchmark",
    labelUr: "لائیو مارکیٹ ریٹ بینچ مارک",
    color: "text-orange-600 dark:text-orange-400",
    bg: "bg-orange-50 dark:bg-orange-900/30",
    position: "top-1/2 right-6",
  },
  {
    icon: FileCheck2,
    label: "FIDIC Risk Detection",
    labelUr: "فڈک قانونی خطرات کی نشاندہی",
    color: "text-blue-600 dark:text-blue-400",
    bg: "bg-blue-50 dark:bg-blue-900/30",
    position: "bottom-16 left-6",
  },
];

export default function HeroSection() {
  const { t } = useLanguage();

  return (
    <section
      id="home"
      className="relative min-h-screen pt-16 flex items-center overflow-hidden bg-white dark:bg-navy-900"
    >
      {/* Blueprint technical grid background */}
      <div
        className="absolute inset-0 opacity-[0.035] dark:opacity-[0.06]"
        style={{
          backgroundImage: `linear-gradient(to right, #0f172a 1px, transparent 1px),
            linear-gradient(to bottom, #0f172a 1px, transparent 1px)`,
          backgroundSize: "60px 60px",
        }}
      />

      <div className="container-custom relative z-10 py-20">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left Content */}
          <div className="space-y-8 animate-fade-in">
            {/* Engineering Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-orange-50 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-800 rounded-full">
              <HardHat className="w-3.5 h-3.5 text-orange-600 dark:text-orange-400" />
              <span className="text-xs font-semibold text-orange-700 dark:text-orange-400 tracking-wide uppercase">
                {t(
                  "Pakistan Construction Intelligence",
                  "پاکستان تعمیراتی انٹیلی جنس پلیٹ فارم"
                )}
              </span>
            </div>

            {/* Headline */}
            <div className="space-y-4">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-navy-900 dark:text-white leading-tight tracking-tight">
                {t(
                  <>
                    Construction <span className="text-orange-500">Intelligence</span>, Structural Safety &amp; Cost Control
                  </>,
                  <>
                    پاکستان کا جدید <span className="text-orange-500">تعمیراتی انٹیلی جنس</span> اور سٹرکچرل سیفٹی نظام
                  </>
                )}
              </h1>
              <p className="text-lg sm:text-xl text-slate-600 dark:text-slate-400 max-w-xl leading-relaxed">
                {t(
                  "Unifying real-time Pakistani market material rates, statutory building codes (PBC, LDA, CDA, SBCA), and deterministic structural safety advisories.",
                  "پاکستان بھر میں لائیو میٹریل ریٹس، عمارتی قوانین اور سٹرکچرل خطرات کے فوری تکنیکی حل کے لیے مستند پلیٹ فارم۔"
                )}
              </p>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-3">
              <Link href="/signup" className="btn-primary px-6 py-3.5 text-base rounded-xl">
                {t("Get Started Free", "مفت اکاؤنٹ بنائیں")}
                <ArrowRight className="w-4 h-4" />
              </Link>
              <a href="#rates" className="btn-secondary px-6 py-3.5 text-base rounded-xl">
                <TrendingUp className="w-4 h-4 text-orange-500" />
                {t("View Live Market Rates", "لائیو مارکیٹ ریٹس دیکھیں")}
              </a>
            </div>

            {/* Factual Technical Metrics */}
            <div className="grid grid-cols-3 gap-6 pt-4 border-t border-slate-100 dark:border-slate-800">
              <div>
                <p className="text-2xl font-black text-navy-900 dark:text-white">PBC 2021</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  {t("Building Code & Bylaws", "بلڈنگ کوڈز و ضوابط")}
                </p>
              </div>
              <div>
                <p className="text-2xl font-black text-navy-900 dark:text-white">38 Rules</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  {t("Structural Hazard Taxonomy", "سٹرکچرل خطرات کی کیٹلاگ")}
                </p>
              </div>
              <div>
                <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400">Canonical</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  {t("Multi-Source Rate Engine", "مستند مارکیٹ ریٹس")}
                </p>
              </div>
            </div>
          </div>

          {/* Right — Hero Imagery & Dynamic Floating Cards */}
          <div className="relative animate-slide-in-right">
            <div className="relative rounded-2xl overflow-hidden shadow-2xl ring-1 ring-slate-200 dark:ring-slate-700">
              <Image
                src="/hero.jpg"
                alt="Civil engineer reviewing construction blueprints with TameerAI"
                width={700}
                height={525}
                className="w-full object-cover"
                priority
              />
              <div className="absolute inset-0 bg-gradient-to-t from-navy-900/30 via-transparent to-transparent" />
            </div>

            {/* Floating Indicators */}
            {floatingCards.map((card) => {
              const Icon = card.icon;
              return (
                <div
                  key={card.label}
                  className={`absolute ${card.position} shadow-lg rounded-xl transition-transform hover:scale-105`}
                >
                  <div className="flex items-center gap-2.5 bg-white/95 dark:bg-navy-900/95 backdrop-blur-md rounded-xl px-3.5 py-2.5 ring-1 ring-slate-200 dark:ring-slate-700 whitespace-nowrap">
                    <div className={`p-1.5 rounded-lg ${card.bg}`}>
                      <Icon className={`w-3.5 h-3.5 ${card.color}`} />
                    </div>
                    <span className="text-xs font-semibold text-navy-900 dark:text-white">
                      {t(card.label, card.labelUr)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
