/* eslint-disable @next/next/no-img-element */
"use client";

import React from "react";
import {
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatHeaderProps {
  activeSessionTitle?: string | null;
  leftSidebarOpen: boolean;
  rightPanelOpen: boolean;
  onToggleLeftSidebar: () => void;
  onToggleRightPanel: () => void;
  language: "en" | "ur";
}

export function ChatHeader({
  activeSessionTitle,
  leftSidebarOpen,
  rightPanelOpen,
  onToggleLeftSidebar,
  onToggleRightPanel,
  language,
}: ChatHeaderProps) {
  const isUrdu = language === "ur";

  return (
    <div
      role="banner"
      className="h-12 px-4 border-b border-slate-200/80 dark:border-slate-800 bg-white dark:bg-navy-950 flex items-center justify-between gap-3 flex-shrink-0 z-10"
    >
      {/* Left: Mascot & Identity */}
      <div className="flex items-center gap-2.5 min-w-0">
        <button
          type="button"
          onClick={onToggleLeftSidebar}
          className="p-1.5 rounded-lg text-slate-500 hover:text-navy-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-navy-800 transition-colors"
          title={isUrdu ? "سیشن ہسٹری کھولیں / بند کریں" : "Toggle History"}
          aria-label={isUrdu ? "سیشن ہسٹری" : "Toggle History"}
        >
          {leftSidebarOpen ? (
            <PanelLeftClose className="w-4 h-4" />
          ) : (
            <PanelLeftOpen className="w-4 h-4" />
          )}
        </button>

        <div className="relative flex items-center flex-shrink-0">
          <img
            src="/orange_robot_mascot.svg"
            alt="TameerAI Assistant"
            width={42}
            height={28}
            className="w-[42px] h-[28px] object-contain flex-shrink-0"
          />
          <span
            className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-500 ring-2 ring-white dark:ring-navy-950"
            title={isUrdu ? "ورک اسپیس فعال" : "Workspace Ready"}
            aria-label={isUrdu ? "ورک اسپیس فعال" : "Workspace Ready"}
          />
        </div>

        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs sm:text-sm font-bold text-navy-900 dark:text-white leading-tight truncate">
              {activeSessionTitle
                ? activeSessionTitle
                : isUrdu
                  ? "تعمیر اے آئی اسسٹنٹ"
                  : "TameerAI Assistant"}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500 dark:text-slate-400 leading-tight font-normal truncate">
            <span>
              {isUrdu
                ? "تعمیراتی رہنمائی ورک اسپیس"
                : "Construction Intelligence Workspace"}
            </span>
            <span className="text-slate-300 dark:text-slate-600 hidden sm:inline">·</span>
            <span className="hidden sm:inline">
              {isUrdu
                ? "پاکستان بلڈنگ کوڈز اور کنسٹرکشن انٹیلیجنس"
                : "Pakistan Building Codes & Construction Intelligence"}
            </span>
          </div>
        </div>
      </div>

      {/* Right: Reference Panel Toggle */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <button
          type="button"
          onClick={onToggleRightPanel}
          className={cn(
            "p-1.5 rounded-lg transition-colors flex items-center gap-1 text-xs font-medium",
            rightPanelOpen
              ? "bg-orange-50 dark:bg-navy-800 text-orange-600 dark:text-orange-400"
              : "text-slate-500 hover:text-navy-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-navy-800"
          )}
          title={isUrdu ? "ریفرنس پینل کھولیں / بند کریں" : "Toggle Reference Panel"}
          aria-label={isUrdu ? "ریفرنس پینل" : "Toggle Reference Panel"}
        >
          {rightPanelOpen ? (
            <PanelRightClose className="w-4 h-4" />
          ) : (
            <PanelRightOpen className="w-4 h-4" />
          )}
        </button>
      </div>
    </div>
  );
}
