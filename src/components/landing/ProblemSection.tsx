"use client";

import { useLanguage } from "@/contexts/LanguageContext";
import { AlertTriangle, TrendingUp, FileWarning } from "lucide-react";

const problems = [
  {
    icon: AlertTriangle,
    en: {
      title: "Building Code Problems",
      desc: "Engineers manually checking hundreds of PBC 2021 clauses — missing critical violations that lead to fines, demolition orders, or structural failures.",
      stat: "67%",
      statLabel: "projects face code violations",
    },
    ur: {
      title: "بلڈنگ کوڈ کے مسائل",
      desc: "انجینئرز دستی طور پر سینکڑوں پی بی سی 2021 شقوں کو چیک کرتے ہیں اور اہم خلاف ورزیاں چھوٹ جاتی ہیں۔",
      stat: "67%",
      statLabel: "منصوبوں میں ضوابط کے مسائل",
    },
    color: "text-red-500",
    bg: "bg-red-50 dark:bg-red-900/20",
    border: "border-red-100 dark:border-red-900/40",
  },
  {
    icon: TrendingUp,
    en: {
      title: "Cost Overruns",
      desc: "Projects exceed budget by 15–40% due to inaccurate BOQs, material price volatility, and poor quantity estimation — costing billions in losses annually.",
      stat: "28%",
      statLabel: "average cost overrun in Pakistan",
    },
    ur: {
      title: "لاگت میں اضافہ (Cost Overruns)",
      desc: "منصوبے غلط بی او کیو، مواد کی قیمت میں اتار چڑھاؤ اور ناقص تخمینے کی وجہ سے بجٹ سے 15-40% تجاوز کرتے ہیں۔",
      stat: "28%",
      statLabel: "پاکستان میں اوسط لاگت تجاوز",
    },
    color: "text-orange-500",
    bg: "bg-orange-50 dark:bg-orange-900/20",
    border: "border-orange-100 dark:border-orange-900/40",
  },
  {
    icon: FileWarning,
    en: {
      title: "Contract Risks",
      desc: "Unfavorable clauses, missing penalty terms, and liability gaps in construction contracts go unnoticed until it's too late — exposing contractors to massive losses.",
      stat: "43%",
      statLabel: "contracts have hidden risk clauses",
    },
    ur: {
      title: "معاہدے کے خطرات",
      desc: "ناموافق شقیں، غائب جرمانے کی شرائط، اور معاہدوں میں ذمہ داری کے خلاء کا تب تک پتہ نہیں چلتا جب بہت دیر ہو جاتی ہے۔",
      stat: "43%",
      statLabel: "معاہدوں میں پوشیدہ خطرناک شقیں",
    },
    color: "text-yellow-500",
    bg: "bg-yellow-50 dark:bg-yellow-900/20",
    border: "border-yellow-100 dark:border-yellow-900/40",
  },
];

export default function ProblemSection() {
  const { t } = useLanguage();

  return (
    <section className="py-24 bg-slate-50 dark:bg-navy-900/50">
      <div className="container-custom">
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-900 rounded-full mb-4">
            <span className="text-xs font-semibold text-red-600 dark:text-red-400 uppercase tracking-wide">
              {t("The Problem", "مسئلہ")}
            </span>
          </div>
          <h2 className="section-title mb-4">
            {t(
              "Pakistan's Construction Industry Is Losing Billions",
              "پاکستان کی تعمیراتی صنعت اربوں روپے کھو رہی ہے"
            )}
          </h2>
          <p className="section-subtitle">
            {t(
              "Manual processes, outdated tools, and lack of AI intelligence are costing contractors, engineers, and developers dearly.",
              "دستی عمل، پرانے اوزار، اور اے آئی انٹیلی جنس کی کمی ٹھیکیداروں، انجینئرز اور ڈویلپرز کو بھاری نقصان اٹھا رہی ہے۔"
            )}
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {problems.map((problem, i) => {
            const Icon = problem.icon;
            const content = t(problem.en, problem.ur) as typeof problem.en;
            return (
              <div
                key={i}
                className={`card p-6 border ${problem.border} group hover:scale-[1.02] transition-transform duration-300`}
              >
                <div className={`w-12 h-12 ${problem.bg} rounded-xl flex items-center justify-center mb-5`}>
                  <Icon className={`w-6 h-6 ${problem.color}`} />
                </div>
                <h3 className="text-lg font-bold text-navy-900 dark:text-white mb-3">
                  {content.title}
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed mb-5">
                  {content.desc}
                </p>
                <div className="pt-4 border-t border-slate-100 dark:border-slate-700">
                  <span className={`text-3xl font-bold ${problem.color}`}>{content.stat}</span>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{content.statLabel}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
