"use client";

import React, { useState } from "react";
import { Calculator, Check, Copy, AlertCircle, FileCheck, Layers } from "lucide-react";
import { FormulaBlock } from "./FormulaBlock";
import { MessageTable } from "./MessageTable";
import { cn } from "@/lib/utils";

export interface CalculationInputParam {
  name: string;
  symbol: string;
  value: string | number;
  unit: string;
  notes?: string;
}

export interface CalculationData {
  title: string;
  inputs: CalculationInputParam[];
  formula: string;
  formulaCaption?: string;
  variables: Array<{ symbol: string; name: string; unit?: string }>;
  substitution: string;
  intermediateSteps: string[];
  finalResult: {
    value: string;
    unit: string;
    highlightText?: string;
  };
  assumptions: string[];
  limitations: string[];
  recommendation?: string;
}

interface CalculationBlockProps {
  data: CalculationData;
  className?: string;
  language?: "en" | "ur";
}

export function CalculationBlock({ data, className, language = "en" }: CalculationBlockProps) {
  const [copied, setCopied] = useState(false);
  const isUrdu = language === "ur";

  // Build clean plain text version for copying
  const handleCopyCalculation = () => {
    const textLines: string[] = [
      `=== ${data.title} ===`,
      "",
      "1. INPUT PARAMETERS:",
      ...data.inputs.map(
        (inp) => `  - ${inp.name} (${inp.symbol}): ${inp.value} ${inp.unit}${inp.notes ? ` [${inp.notes}]` : ""}`
      ),
      "",
      `2. GOVERNING FORMULA: ${data.formula}`,
      "",
      "3. VARIABLE DEFINITIONS:",
      ...data.variables.map((v) => `  - ${v.symbol}: ${v.name}${v.unit ? ` (${v.unit})` : ""}`),
      "",
      `4. SUBSTITUTION: ${data.substitution}`,
      "",
      "5. INTERMEDIATE STEPS:",
      ...data.intermediateSteps.map((step, idx) => `  Step ${idx + 1}: ${step}`),
      "",
      `6. FINAL RESULT: ${data.finalResult.value} ${data.finalResult.unit}${
        data.finalResult.highlightText ? ` (${data.finalResult.highlightText})` : ""
      }`,
      "",
      "7. ASSUMPTIONS:",
      ...data.assumptions.map((a) => `  - ${a}`),
      "",
      "8. LIMITATIONS:",
      ...data.limitations.map((l) => `  - ${l}`),
      ...(data.recommendation ? ["", `9. RECOMMENDATION: ${data.recommendation}`] : []),
      "",
      "Notice: Verification by a licensed PEC Professional Engineer is required prior to execution.",
    ];

    navigator.clipboard.writeText(textLines.join("\n"));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Convert inputs to table format for MessageTable
  const inputHeaders = isUrdu
    ? ["پیرامیٹر", "علامت", "قیمت", "یونٹ", "تفصیل"]
    : ["Parameter", "Symbol", "Value", "Unit", "Notes"];

  const inputRows = data.inputs.map((inp) => [
    inp.name,
    inp.symbol,
    String(inp.value),
    inp.unit,
    inp.notes || "-",
  ]);

  return (
    <div
      data-testid="calculation-block"
      className={cn(
        "my-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 shadow-xs overflow-hidden",
        className
      )}
    >
      {/* 1. Header with Title & Action */}
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-orange-500/10 via-slate-50 to-slate-50 dark:from-orange-500/10 dark:via-navy-900 dark:to-navy-900 border-b border-slate-200/80 dark:border-slate-800">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-orange-500 text-white flex items-center justify-center flex-shrink-0 shadow-2xs">
            <Calculator className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-orange-100 text-orange-800 dark:bg-orange-950/80 dark:text-orange-300 border border-orange-200 dark:border-orange-800">
                {isUrdu ? "انجینئرنگ حساب کتاب" : "Engineering Calculation"}
              </span>
            </div>
            <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 truncate mt-0.5">
              {data.title}
            </h4>
          </div>
        </div>

        <button
          type="button"
          onClick={handleCopyCalculation}
          className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-navy-950 hover:bg-slate-100 dark:hover:bg-navy-900 text-slate-700 dark:text-slate-300 transition-colors flex-shrink-0 ml-2"
          title={isUrdu ? "مکمل حساب کتاب کاپی کریں" : "Copy complete calculation"}
          aria-label="Copy calculation"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-500" />
              <span className="text-emerald-600 dark:text-emerald-400 font-medium">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-slate-500" />
              <span>{isUrdu ? "کاپی کریں" : "Copy"}</span>
            </>
          )}
        </button>
      </div>

      <div className="p-4 sm:p-5 space-y-4 text-xs">
        {/* 2. Input Parameters Table */}
        <section className="space-y-1.5">
          <div className="flex items-center gap-1.5 font-bold text-slate-800 dark:text-slate-200 text-xs">
            <Layers className="w-3.5 h-3.5 text-orange-500" />
            <span>{isUrdu ? "1. بنیادی پیرامیٹرز اور قیمتیں" : "1. Input Parameters"}</span>
          </div>
          <MessageTable
            headers={inputHeaders}
            rows={inputRows}
            caption={isUrdu ? "حساباتی ان پٹ ٹیبل" : "Calculation Design Inputs"}
          />
        </section>

        {/* 3. Governing Formula */}
        <section className="space-y-1.5">
          <div className="font-bold text-slate-800 dark:text-slate-200 text-xs">
            {isUrdu ? "2. مروجہ انجینئرنگ فارمولا" : "2. Governing Formula"}
          </div>
          <FormulaBlock formula={data.formula} caption={data.formulaCaption} />
        </section>

        {/* 4. Variable Definitions */}
        {data.variables && data.variables.length > 0 && (
          <section className="space-y-1.5 bg-slate-50/60 dark:bg-navy-900/40 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
            <div className="font-bold text-slate-700 dark:text-slate-300 text-[11px] uppercase tracking-wide">
              {isUrdu ? "3. متغیرات کی تعریف" : "3. Variable Definitions"}
            </div>
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-700 dark:text-slate-300">
              {data.variables.map((v, i) => (
                <li key={i} className="flex items-center gap-1.5">
                  <span className="font-serif italic font-bold text-orange-600 dark:text-orange-400">
                    {v.symbol}
                  </span>
                  <span>:</span>
                  <span>{v.name}</span>
                  {v.unit && <span className="text-slate-400 text-[11px]">({v.unit})</span>}
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* 5. Step-by-Step Substitution */}
        <section className="space-y-1.5">
          <div className="font-bold text-slate-800 dark:text-slate-200 text-xs">
            {isUrdu ? "4. فارمولے میں قیمتوں کا متبادل" : "4. Numerical Substitution"}
          </div>
          <div className="p-3 rounded-xl bg-orange-50/40 dark:bg-orange-950/20 border border-orange-200/60 dark:border-orange-900/40 font-mono text-xs text-slate-900 dark:text-slate-100 overflow-x-auto">
            {data.substitution}
          </div>
        </section>

        {/* 6. Intermediate Calculation Steps */}
        {data.intermediateSteps && data.intermediateSteps.length > 0 && (
          <section className="space-y-1.5">
            <div className="font-bold text-slate-800 dark:text-slate-200 text-xs">
              {isUrdu ? "5. درمیانی مراحل اور تفاصیل" : "5. Intermediate Calculations"}
            </div>
            <ol className="space-y-1.5 list-decimal list-inside text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-navy-900/40 p-3 rounded-xl border border-slate-200/60 dark:border-slate-800">
              {data.intermediateSteps.map((step, idx) => (
                <li key={idx} className="leading-relaxed">
                  <span className="font-sans">{step}</span>
                </li>
              ))}
            </ol>
          </section>
        )}

        {/* 7. Final Result */}
        <section className="p-4 rounded-xl bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border border-emerald-500/30 text-emerald-950 dark:text-emerald-200 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">
              {isUrdu ? "6. حتمی نتیجہ" : "6. Final Computed Result"}
            </span>
            <FileCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div className="flex flex-wrap items-baseline gap-2 pt-1">
            <span className="text-xl sm:text-2xl font-bold font-mono text-emerald-700 dark:text-emerald-300">
              {data.finalResult.value}
            </span>
            <span className="text-sm font-semibold text-emerald-800 dark:text-emerald-200">
              {data.finalResult.unit}
            </span>
          </div>
          {data.finalResult.highlightText && (
            <p className="text-xs text-emerald-900 dark:text-emerald-100 pt-1 border-t border-emerald-500/20 font-medium">
              {data.finalResult.highlightText}
            </p>
          )}
        </section>

        {/* 8. Assumptions & 9. Limitations */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-900/40 border border-slate-200/80 dark:border-slate-800 space-y-1">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
              {isUrdu ? "7. انجینئرنگ مفروضات" : "7. Assumptions"}
            </div>
            <ul className="list-disc list-inside space-y-1 text-slate-700 dark:text-slate-300 text-[11px]">
              {data.assumptions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>

          <div className="p-3 rounded-xl bg-amber-50/40 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40 space-y-1">
            <div className="text-[11px] font-bold uppercase tracking-wider text-amber-800 dark:text-amber-300 flex items-center gap-1">
              <AlertCircle className="w-3 h-3 text-amber-600" />
              <span>{isUrdu ? "8. عملی حدود اور شرائط" : "8. Limitations"}</span>
            </div>
            <ul className="list-disc list-inside space-y-1 text-slate-700 dark:text-slate-300 text-[11px]">
              {data.limitations.map((l, i) => (
                <li key={i}>{l}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* 10. Practical Recommendation */}
        {data.recommendation && (
          <div className="p-3 rounded-xl bg-blue-50/40 dark:bg-blue-950/20 border border-blue-200/60 dark:border-blue-900/40 text-blue-950 dark:text-blue-200 text-xs">
            <span className="font-bold mr-1">
              {isUrdu ? "9. عملی انجینئرنگ مشورہ:" : "9. Recommendation:"}
            </span>
            <span>{data.recommendation}</span>
          </div>
        )}

        {/* Verification Footer Notice */}
        <div className="text-[10px] text-slate-400 italic pt-1 border-t border-slate-100 dark:border-slate-800/80">
          {isUrdu
            ? "نوٹ: یہ حساب کتاب تخمینہ جاتی رہنمائی کے لیے ہے۔ سائٹ پر کنکریٹ ڈالنے سے قبل پی ای سی مجاز سٹرکچرل انجینئر کی توثیق ضروری ہے۔"
            : "Notice: Calculated for advisory and quantity estimation purposes. Must be verified and signed off by a licensed PEC Professional Structural Engineer before procurement and concrete placement."}
        </div>
      </div>
    </div>
  );
}

