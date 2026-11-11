/* eslint-disable @next/next/no-img-element */
"use client";

import React from "react";
import { Info } from "lucide-react";
import { EngineeringShortcutGrid } from "./EngineeringShortcutGrid";

interface ChatWelcomeProps {
  language: "en" | "ur";
}

export function ChatWelcome({ language }: ChatWelcomeProps) {
  const isUrdu = language === "ur";

  return (
    <div
      data-testid="chat-welcome"
      className="flex flex-col items-center justify-center min-h-full py-4 sm:py-6 px-4 text-center max-w-4xl mx-auto space-y-3 sm:space-y-4"
    >
      {/* Official Mascot */}
      <img
        src="/orange_robot_mascot.svg"
        alt="TameerAI Assistant"
        width={72}
        height={48}
        className="w-[72px] h-[48px] object-contain flex-shrink-0 mb-1"
      />

      {/* Main Heading & Description */}
      <div className="space-y-1">
        <h2 className="text-lg sm:text-xl md:text-2xl font-bold text-navy-900 dark:text-white tracking-tight">
          {isUrdu ? "آج تعمیر اے آئی آپ کی کیا مدد کر سکتا ہے؟" : "How can TameerAI help you today?"}
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto">
          {isUrdu
            ? "آپ کا کنسٹرکشن اور انجینئرنگ انٹیلیجنس ورک سپیس۔"
            : "Your construction and engineering intelligence workspace."}
        </p>
      </div>

      {/* Six Engineering Shortcut Cards */}
      <EngineeringShortcutGrid language={language} />

      {/* Assistant Capability Disclosure Notice */}
      <div className="pt-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100/80 dark:bg-navy-900/80 border border-slate-200/80 dark:border-slate-800 text-[10px] sm:text-[11px] text-slate-600 dark:text-slate-300 max-w-xl text-center">
          <Info className="w-3.5 h-3.5 text-orange-500 flex-shrink-0" />
          <span>
            {isUrdu ? (
              <>
                موجودہ موڈ: خودکار انجینئرنگ رہنمائی۔ ریگولیٹری حوالہ جات کی آزادانہ تصدیق ضروری ہے۔ (
                <span>پاکستان بلڈنگ کوڈز اور کنسٹرکشن انٹیلیجنس</span>)
              </>
            ) : (
              <>
                Current mode: Deterministic engineering guidance. Regulatory references require independent source verification (
                <span>Pakistan Building Codes & Construction Intelligence</span>).
              </>
            )}
          </span>
        </div>
      </div>
    </div>
  );
}
