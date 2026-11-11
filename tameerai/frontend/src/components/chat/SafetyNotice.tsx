"use client";

import React from "react";
import { Info, AlertTriangle, ShieldAlert, AlertOctagon, Scale } from "lucide-react";
import { cn } from "@/lib/utils";

export type SafetySeverity = "info" | "caution" | "warning" | "critical";

export interface SafetyNoticeProps {
  level: SafetySeverity;
  title?: string;
  message: string;
  codeReference?: string;
  clause?: string;
  className?: string;
  language?: "en" | "ur";
}

const SEVERITY_CONFIG: Record<
  SafetySeverity,
  {
    icon: React.ElementType;
    badgeEn: string;
    badgeUr: string;
    containerClass: string;
    badgeClass: string;
    iconClass: string;
    borderClass: string;
  }
> = {
  info: {
    icon: Info,
    badgeEn: "Engineering Note",
    badgeUr: "انجینئرنگ نوٹ",
    containerClass: "bg-blue-50/60 dark:bg-blue-950/30 text-blue-950 dark:text-blue-200 border-blue-200 dark:border-blue-900/60",
    badgeClass: "bg-blue-100 text-blue-800 dark:bg-blue-900/60 dark:text-blue-300 border-blue-300 dark:border-blue-800",
    iconClass: "text-blue-600 dark:text-blue-400",
    borderClass: "border-l-4 border-l-blue-500",
  },
  caution: {
    icon: AlertTriangle,
    badgeEn: "Engineering Caution",
    badgeUr: "تکنیکی احتیاط",
    containerClass: "bg-amber-50/60 dark:bg-amber-950/30 text-amber-950 dark:text-amber-200 border-amber-200 dark:border-amber-900/60",
    badgeClass: "bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-300 border-amber-300 dark:border-amber-800",
    iconClass: "text-amber-600 dark:text-amber-400",
    borderClass: "border-l-4 border-l-amber-500",
  },
  warning: {
    icon: AlertTriangle,
    badgeEn: "Compliance Warning",
    badgeUr: "تعمیل وارننگ",
    containerClass: "bg-orange-50/60 dark:bg-orange-950/30 text-orange-950 dark:text-orange-200 border-orange-200 dark:border-orange-900/60",
    badgeClass: "bg-orange-100 text-orange-800 dark:bg-orange-900/60 dark:text-orange-300 border-orange-300 dark:border-orange-800",
    iconClass: "text-orange-600 dark:text-orange-400",
    borderClass: "border-l-4 border-l-orange-500",
  },
  critical: {
    icon: AlertOctagon,
    badgeEn: "Critical Safety Alert",
    badgeUr: "انتہائی اہم حفاظتی تنبیہ",
    containerClass: "bg-rose-50/60 dark:bg-rose-950/30 text-rose-950 dark:text-rose-200 border-rose-200 dark:border-rose-900/60",
    badgeClass: "bg-rose-100 text-rose-800 dark:bg-rose-900/60 dark:text-rose-300 border-rose-300 dark:border-rose-800",
    iconClass: "text-rose-600 dark:text-rose-400",
    borderClass: "border-l-4 border-l-rose-500",
  },
};

export function SafetyNotice({
  level = "warning",
  title,
  message,
  codeReference,
  clause,
  className,
  language = "en",
}: SafetyNoticeProps) {
  const isUrdu = language === "ur";
  const config = SEVERITY_CONFIG[level] || SEVERITY_CONFIG.warning;
  const IconComponent = config.icon;

  return (
    <aside
      data-testid={`safety-notice-${level}`}
      role="alert"
      className={cn(
        "my-3.5 p-3.5 sm:p-4 rounded-xl border shadow-2xs transition-all",
        config.containerClass,
        config.borderClass,
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn("p-1.5 rounded-lg bg-white/80 dark:bg-navy-900/80 shadow-2xs flex-shrink-0 mt-0.5", config.iconClass)}>
          <IconComponent className="w-4 h-4" />
        </div>

        <div className="flex-1 min-w-0 space-y-1.5">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={cn(
                "inline-flex items-center text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md border",
                config.badgeClass
              )}
            >
              {isUrdu ? config.badgeUr : config.badgeEn}
            </span>
            {title && (
              <h5 className="text-xs font-bold tracking-tight text-slate-900 dark:text-slate-100">
                {title}
              </h5>
            )}
          </div>

          <p className="text-xs leading-relaxed text-slate-800 dark:text-slate-200 font-sans">
            {message}
          </p>

          {codeReference && (
            <div className="pt-1.5 flex items-center gap-1.5 text-[11px] font-mono text-slate-600 dark:text-slate-400">
              <Scale className="w-3 h-3 text-orange-500 flex-shrink-0" />
              <span>
                {codeReference} {clause ? `· ${clause}` : ""}
              </span>
            </div>
          )}

          {/* Transparent Independent Verification Notice */}
          <div className="pt-2 border-t border-slate-200/50 dark:border-slate-800/50 text-[10px] text-slate-500 dark:text-slate-400 italic">
            {isUrdu
              ? "قانونی تنبیہ: یہ رہنمائی پاکستان بلڈنگ کوڈ کے مستند ضوابط پر مبنی ہے۔ سائٹ پر عمل درآمد سے قبل پی ای سی رجسٹرڈ سٹرکچرل انجینئر سے تصدیق لازمی ہے۔"
              : "Advisory Notice: Generated via deterministic rule-based evaluation. Does not replace mandatory physical inspection, soil investigation, or structural endorsement by a PEC-licensed Professional Engineer."}
          </div>
        </div>
      </div>
    </aside>
  );
}

