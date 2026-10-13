"use client";

import { useLanguage } from "@/contexts/LanguageContext";
import Link from "next/link";
import Image from "next/image";
import { ArrowRight, Play, ShieldCheck, AlertTriangle, FileCheck } from "lucide-react";

const floatingCards = [
  {
    icon: ShieldCheck,
    label: "PBC 2021 Verified",
    labelUr: "پی بی سی 2021 تصدیق شدہ",
    color: "text-green-600 dark:text-green-400",
    bg: "bg-green-50 dark:bg-green-900/30",
    position: "top-8 left-8",
  },
  {
    icon: AlertTriangle,
    label: "Cost Risk Detection",
    labelUr: "لاگت کا خطرہ شناخت",
    color: "text-orange-600 dark:text-orange-400",
    bg: "bg-orange-50 dark:bg-orange-900/30",
    position: "top-1/2 right-6",
  },
  {
    icon: FileCheck,
    label: "AI Report Generated",
    labelUr: "اے آئی رپورٹ تیار",
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
      {/* Subtle background grid */}
      <div
        className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05]"
        style={{
          backgroundImage: `linear-gradient(to right, #0f172a 1px, transparent 1px),
            linear-gradient(to bottom, #0f172a 1px, transparent 1px)`,
          backgroundSize: "60px 60px",
        }}
      />

      {/* Gradient orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-orange-500/5 dark:bg-orange-500/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-green-500/5 dark:bg-green-500/10 rounded-full blur-3xl" />

      <div className="container-custom relative z-10 py-20">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left Content */}
          <div className="space-y-8 animate-fade-in">
            {/* Pill badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-orange-50 dark:bg-orange-900/30 border border-orange-100 dark:border-orange-800 rounded-full">
              <span className="w-1.5 h-1.5 bg-orange-500 rounded-full animate-pulse" />
              <span className="text-xs font-semibold text-orange-600 dark:text-orange-400 tracking-wide uppercase">
                {t("Pakistan's #1 Construction AI", "پاکستان کا نمبر 1 تعمیراتی اے آئی")}
              </span>
            </div>

            {/* Headline */}
            <div className="space-y-4">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-navy-900 dark:text-white leading-tight tracking-tight">
                {t(
                  <>
                    Pakistan&apos;s <span className="gradient-text">AI Construction</span> Compliance &amp; Cost Intelligence
                  </>,
                  <>
                    پاکستان کا <span className="gradient-text">اے آئی تعمیراتی</span> تعمیل اور لاگت انٹیلی جنس سسٹم
                  </>
                )}
              </h1>
              <p className="text-lg sm:text-xl text-slate-500 dark:text-slate-400 max-w-xl leading-relaxed">
                {t(
                  "Analyze building codes, contracts and construction costs with AI.",
                  "عمارتی ضوابط، معاہدات اور تعمیراتی اخراجات کا اے آئی سے تجزیہ کریں۔"
                )}
              </p>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-3">
              <Link href="/signup" className="btn-primary px-6 py-3.5 text-base">
                {t("Start New Audit", "نیا آڈٹ شروع کریں")}
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/dashboard/ai-assistant" className="btn-secondary px-6 py-3.5 text-base">
                <Play className="w-4 h-4 text-orange-500" />
                {t("Try AI Assistant", "اے آئی اسسٹنٹ آزمائیں")}
              </Link>
            </div>

            {/* Trust metrics */}
            <div className="flex items-center gap-6 pt-2">
              {[
                { value: "500+", label: t("Projects Analyzed", "تجزیہ شدہ منصوبے") },
                { value: "PBC 2021", label: t("Certified", "سرٹیفائیڈ") },
                { value: "98%", label: t("Accuracy Rate", "درستگی کی شرح") },
              ].map((stat) => (
                <div key={stat.value} className="text-center">
                  <p className="text-xl font-bold text-navy-900 dark:text-white">{stat.value}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right — Hero Image with floating cards */}
          <div className="relative animate-slide-in-right">
            <div className="relative rounded-2xl overflow-hidden shadow-2xl ring-1 ring-slate-200 dark:ring-slate-700">
              <Image
                src="/hero.jpg"
                alt="Civil engineer using TameerAI on construction site"
                width={700}
                height={525}
                className="w-full object-cover"
                priority
              />
              {/* Overlay gradient */}
              <div className="absolute inset-0 bg-gradient-to-t from-navy-900/20 via-transparent to-transparent" />
            </div>

            {/* Floating Cards */}
            {floatingCards.map((card) => {
              const Icon = card.icon;
              return (
                <div
                  key={card.label}
                  className={`absolute ${card.position} animate-float`}
                  style={{
                    animationDelay: floatingCards.indexOf(card) * 0.7 + "s",
                  }}
                >
                  <div className="flex items-center gap-2.5 bg-white dark:bg-navy-800 rounded-xl px-3.5 py-2.5 shadow-lg ring-1 ring-slate-200 dark:ring-slate-700 whitespace-nowrap">
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
