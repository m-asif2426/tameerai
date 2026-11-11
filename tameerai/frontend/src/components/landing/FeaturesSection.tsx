"use client";

import { useLanguage } from "@/contexts/LanguageContext";
import {
  ShieldCheck, FileText, TrendingUp, MessageSquare, BookOpen, BarChart3
} from "lucide-react";

const features = [
  {
    icon: MessageSquare,
    en: {
      title: "AI Assistant",
      desc: "Ask construction, structural, and geotechnical questions 24/7. Get instant expert answers with citations from PBC 2021, ACI 318, and ASTM standards.",
    },
    ur: {
      title: "اے آئی اسسٹنٹ (AI Assistant)",
      desc: "24/7 تعمیراتی اور انجینئرنگ سوالات پوچھیں۔ پی بی سی 2021 اور اے سی آئی 318 کے درست حوالوں کے ساتھ فوری جوابات حاصل کریں۔",
    },
    color: "text-orange-600 dark:text-orange-400",
    bg: "bg-orange-50 dark:bg-orange-900/20",
    badge: { en: "Intelligent", ur: "ذہین" },
    badgeColor: "badge-orange",
  },
  {
    icon: ShieldCheck,
    en: {
      title: "Compliance Check",
      desc: "Automated verification against Building Code of Pakistan (PBC 2021), CDA, LDA, and SBCA bylaws. Flag code violations before municipal submission.",
    },
    ur: {
      title: "تعمیل کی جانچ (Compliance Check)",
      desc: "بلڈنگ کوڈ آف پاکستان (PBC 2021)، ایل ڈی اے اور سی ڈی اے ضوابط کی خودکار جانچ۔ نقشہ جمع کرانے سے پہلے غلطیوں کی نشاندہی۔",
    },
    color: "text-green-600 dark:text-green-400",
    bg: "bg-green-50 dark:bg-green-900/20",
    badge: { en: "PBC 2021", ur: "پی بی سی 2021" },
    badgeColor: "badge-green",
  },
  {
    icon: FileText,
    en: {
      title: "Contract Analysis",
      desc: "Scan contractor, subcontractor, and FIDIC contracts for liability traps, missing penalty clauses, delay damages, and unfavorable payment terms.",
    },
    ur: {
      title: "معاہدے کا تجزیہ (Contract Analysis)",
      desc: "ٹھیکیداروں اور فیڈک معاہدات میں قانونی خطرات، غیر منصفانہ شرائط، اور جرمانے کی غیر واضح شقوں کا فوری سراغ لگائیں۔",
    },
    color: "text-blue-600 dark:text-blue-400",
    bg: "bg-blue-50 dark:bg-blue-900/20",
    badge: { en: "Risk Guard", ur: "رسک گارڈ" },
    badgeColor: "badge-orange",
  },
  {
    icon: TrendingUp,
    en: {
      title: "Cost Intelligence",
      desc: "Real-time market rates for steel, cement, and bricks across Lahore, Karachi, and Islamabad. BOQ verification and AI budget variance forecasting.",
    },
    ur: {
      title: "لاگت انٹیلی جنس (Cost Intelligence)",
      desc: "لاہور، کراچی، اور اسلام آباد میں سٹیل، سیمنٹ اور اینٹوں کے لائیو ریٹس۔ بی او کیو تخمینہ اور بجٹ تجاوز کی پیشن گوئی۔",
    },
    color: "text-emerald-600 dark:text-emerald-400",
    bg: "bg-emerald-50 dark:bg-emerald-900/20",
    badge: { en: "Live Rates", ur: "لائیو ریٹس" },
    badgeColor: "badge-green",
  },
  {
    icon: BookOpen,
    en: {
      title: "Urdu Support",
      desc: "Engineered specifically for Pakistan's market. Communicate seamlessly in Urdu (اردو) or Roman Urdu for thekedars, site supervisors, and project owners.",
    },
    ur: {
      title: "اردو سپورٹ (Urdu Support)",
      desc: "خاص طور پر پاکستان کے لیے۔ ٹھیکیداروں، انجینئرز، اور سائیٹ سپروائزرز کے لیے مکمل اردو اور رومن اردو میں بات چیت کی سہولت۔",
    },
    color: "text-purple-600 dark:text-purple-400",
    bg: "bg-purple-50 dark:bg-purple-900/20",
    badge: { en: "Bilingual", ur: "دو لسانی" },
    badgeColor: "badge-orange",
  },
  {
    icon: BarChart3,
    en: {
      title: "Reports",
      desc: "Export investor-grade, bank-compliant PDF reports with audit stamps, clause citation checklists, risk gauges, and executive summaries.",
    },
    ur: {
      title: "پیشہ ورانہ رپورٹس (Reports)",
      desc: "بینکوں، سرمایہ کاروں اور کلائنٹس کے لیے آڈٹ مہر، چیک لسٹ اور ایگزیکٹو سمری کے ساتھ پیشہ ورانہ پی ڈی ایف رپورٹس تیار کریں۔",
    },
    color: "text-cyan-600 dark:text-cyan-400",
    bg: "bg-cyan-50 dark:bg-cyan-900/20",
    badge: { en: "PDF Export", ur: "پی ڈی ایف ایکسپورٹ" },
    badgeColor: "badge-green",
  },
];

export default function FeaturesSection() {
  const { t } = useLanguage();

  return (
    <section id="features" className="py-24 bg-white dark:bg-navy-900">
      <div className="container-custom">
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-orange-50 dark:bg-orange-900/20 border border-orange-100 dark:border-orange-900 rounded-full mb-4">
            <span className="text-xs font-semibold text-orange-600 dark:text-orange-400 uppercase tracking-wide">
              {t("Features", "خصوصیات")}
            </span>
          </div>
          <h2 className="section-title mb-4">
            {t("Everything You Need to Build Smarter", "سمارٹ تعمیر کے لیے سب کچھ")}
          </h2>
          <p className="section-subtitle">
            {t(
              "Six powerful AI tools designed specifically for Pakistan's construction professionals.",
              "پاکستان کے تعمیراتی پیشہ ور افراد کے لیے خاص طور پر ڈیزائن کیے گئے چھ طاقتور اے آئی ٹولز۔"
            )}
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => {
            const Icon = feature.icon;
            const content = t(feature.en, feature.ur) as typeof feature.en;
            const badge = feature.badge ? t(feature.badge.en, feature.badge.ur) as string : null;
            return (
              <div
                key={i}
                className="card p-6 group hover:scale-[1.02] transition-all duration-300 cursor-pointer"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-11 h-11 ${feature.bg} rounded-xl flex items-center justify-center`}>
                    <Icon className={`w-5 h-5 ${feature.color}`} />
                  </div>
                  {badge && (
                    <span className={`${feature.badgeColor} text-xs`}>{badge}</span>
                  )}
                </div>
                <h3 className="text-base font-bold text-navy-900 dark:text-white mb-2">
                  {content.title}
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  {content.desc}
                </p>
                <div className="mt-4 flex items-center gap-1 text-orange-500 text-xs font-semibold group-hover:gap-2 transition-all">
                  {t("Learn more", "مزید جانیں")} →
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
