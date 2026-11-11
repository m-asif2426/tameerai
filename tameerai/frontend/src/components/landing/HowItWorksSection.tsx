"use client";

import { useLanguage } from "@/contexts/LanguageContext";
import {
  FolderPlus,
  UploadCloud,
  Cpu,
  FileCheck2,
  ArrowRight,
  CheckCircle2,
  Sparkles,
} from "lucide-react";

const steps = [
  {
    step: "01",
    icon: FolderPlus,
    badge: "Step 1",
    en: {
      title: "Create Project",
      subtitle: "Setup Project Profile",
      desc: "Specify project type (High-Rise, Commercial, Residential), location (Lahore, Karachi, Islamabad), and governing regulatory body (PBC 2021, LDA, CDA, SBCA).",
      previewLabel: "Configured: G+14 Commercial Plaza, Lahore",
    },
    ur: {
      title: "پروجیکٹ بنائیں (Create Project)",
      subtitle: "پروجیکٹ پروفائل بنائیں",
      desc: "پروجیکٹ کی نوعیت (کمرشل، رہائشی، ہائی رائز)، مقام (لاہور، اسلام آباد، کراچی) اور بلڈنگ اتھارٹی (پی بی سی، ایل ڈی اے، سی ڈی اے) منتخب کریں۔",
      previewLabel: "ترتیب دی گئی: G+14 کمرشل پلازہ، لاہور",
    },
    accentColor: "from-orange-500 to-amber-500",
    iconBg: "bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20",
  },
  {
    step: "02",
    icon: UploadCloud,
    badge: "Step 2",
    en: {
      title: "Upload Documents",
      subtitle: "Drawings, Contracts & BOQs",
      desc: "Drag & drop architectural CAD drawings (.DWG/.DXF), structural PDF blueprints, subcontractor FIDIC contracts, and BOQ material sheets.",
      previewLabel: "Supported: PDF, DWG, DXF, XLSX",
    },
    ur: {
      title: "دستاویزات اپ لوڈ کریں (Upload Documents)",
      subtitle: "ڈرائنگز، معاہدات اور بی او کیو",
      desc: "آرکیٹیکچرل سی اے ڈی ڈرائنگز، سٹرکچرل پی ڈی ایف، ٹھیکیداروں کے قانونی معاہدات اور بی او کیو شیٹس باآسانی ڈریگ اینڈ ڈراپ کریں۔",
      previewLabel: "معاون فارمیٹس: PDF, DWG, DXF, XLSX",
    },
    accentColor: "from-blue-500 to-cyan-500",
    iconBg: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
  },
  {
    step: "03",
    icon: Cpu,
    badge: "Step 3",
    en: {
      title: "AI Analysis",
      subtitle: "Multi-Engine Deep Verification",
      desc: "TameerAI cross-checks dimensions against 1,200+ PBC 2021 clauses, audits rate variances with real-time markets, and flags hazardous contract clauses.",
      previewLabel: "Processing: 34 building code checks / sec",
    },
    ur: {
      title: "اے آئی تجزیہ (AI Analysis)",
      subtitle: "ڈیپ نیورل تصدیق",
      desc: "TameerAI نقشے کی پیمائش کو 1200+ پی بی سی شقوں کے خلاف چیک کرتا ہے، مارکیٹ ریٹس کا تقابل کرتا ہے اور قانونی خطرات کو نمایاں کرتا ہے۔",
      previewLabel: "پراسیسنگ: 34 بلڈنگ کوڈ چیکس فی سیکنڈ",
    },
    accentColor: "from-emerald-500 to-green-500",
    iconBg: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
  },
  {
    step: "04",
    icon: FileCheck2,
    badge: "Step 4",
    en: {
      title: "Generate Report",
      subtitle: "Investor & Municipal Ready",
      desc: "Receive actionable, certified PDF audits complete with clause citations, visual risk scores, estimated cost savings, and stamped executive clearance.",
      previewLabel: "Ready: One-Click Verified PDF Export",
    },
    ur: {
      title: "رپورٹ تیار کریں (Generate Report)",
      subtitle: "سرٹیفائیڈ پی ڈی ایف آڈٹ",
      desc: "قانونی حوالوں، خطرے کے اسکور، لاگت کی ممکنہ بچت اور مہر شدہ سرٹیفکیٹ کے ساتھ مکمل پیشہ ورانہ پی ڈی ایف رپورٹ حاصل کریں۔",
      previewLabel: "تیار: ون کلک تصدیق شدہ پی ڈی ایف برآمد",
    },
    accentColor: "from-purple-500 to-indigo-500",
    iconBg: "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20",
  },
];

export default function HowItWorksSection() {
  const { t } = useLanguage();

  return (
    <section id="how-it-works" className="py-24 bg-slate-50 dark:bg-navy-950 relative overflow-hidden">
      {/* Background ambient gradient glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[300px] bg-orange-500/5 dark:bg-orange-500/10 blur-[140px] pointer-events-none" />

      <div className="container-custom relative z-10">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-orange-50 dark:bg-orange-950/60 border border-orange-200 dark:border-orange-800/80 rounded-full mb-4">
            <Sparkles className="w-3.5 h-3.5 text-orange-500 animate-pulse" />
            <span className="text-xs font-semibold text-orange-600 dark:text-orange-400 uppercase tracking-wider">
              {t("How It Works", "کیسے کام کرتا ہے")}
            </span>
          </div>
          <h2 className="section-title mb-4">
            {t("Four Simple Steps to Total Construction Assurance", "تعمیراتی یقین دہانی کے چار آسان مراحل")}
          </h2>
          <p className="section-subtitle max-w-2xl mx-auto">
            {t(
              "From raw blueprint and contracts to fully audited compliance reports in minutes.",
              "ابتدائی نقشوں اور معاہدات سے منٹوں میں مکمل آڈٹ شدہ تعمیل رپورٹس تک۔"
            )}
          </p>
        </div>

        {/* Step Cards Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 relative">
          {steps.map((item, idx) => {
            const Icon = item.icon;
            const content = t(item.en, item.ur) as typeof item.en;

            return (
              <div
                key={item.step}
                className="group relative bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-xl hover:border-orange-400/50 dark:hover:border-orange-500/40 transition-all duration-300 flex flex-col justify-between"
              >
                {/* Step Pill & Top Line */}
                <div>
                  <div className="flex items-center justify-between mb-5">
                    <span className="text-3xl font-black tracking-tight text-slate-200 dark:text-slate-800 group-hover:text-orange-500/40 transition-colors">
                      {item.step}
                    </span>
                    <span className="px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 group-hover:bg-orange-500 group-hover:text-white transition-all">
                      {item.badge}
                    </span>
                  </div>

                  {/* Icon */}
                  <div
                    className={`w-12 h-12 rounded-xl flex items-center justify-center border mb-4 transition-transform duration-300 group-hover:scale-110 ${item.iconBg}`}
                  >
                    <Icon className="w-6 h-6" />
                  </div>

                  {/* Title & Subtitle */}
                  <h3 className="text-lg font-bold text-navy-900 dark:text-white mb-1 group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors">
                    {content.title}
                  </h3>
                  <p className="text-xs font-semibold text-slate-400 dark:text-slate-500 mb-3 uppercase tracking-wider">
                    {content.subtitle}
                  </p>

                  {/* Description */}
                  <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed mb-6">
                    {content.desc}
                  </p>
                </div>

                {/* Micro preview status bar */}
                <div className="pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                  <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 truncate">
                    {content.previewLabel}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Bottom Fast Action Prompt */}
        <div className="mt-14 text-center">
          <div className="inline-flex items-center gap-3 px-5 py-3 rounded-xl bg-orange-50 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-900/60 text-sm text-slate-700 dark:text-slate-300">
            <span className="font-semibold text-orange-600 dark:text-orange-400">
              {t("Ready to test your project?", "کیا آپ اپنے پروجیکٹ کا جائزہ لینے کے لیے تیار ہیں؟")}
            </span>
            <span className="text-slate-400 dark:text-slate-600">|</span>
            <a
              href="/signup"
              className="font-bold text-navy-900 dark:text-white hover:text-orange-500 dark:hover:text-orange-400 inline-flex items-center gap-1 transition-colors"
            >
              {t("Run Your First AI Audit Free", "پہلا مفت اے آئی آڈٹ چلائیں")}
              <ArrowRight className="w-4 h-4 ml-0.5" />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
