"use client";

import React from "react";
import Link from "next/link";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export interface EngineeringShortcutCardProps {
  id: string;
  title: string;
  titleUrdu: string;
  description: string;
  descriptionUrdu: string;
  href: string;
  icon: LucideIcon;
  language: "en" | "ur";
}

export function EngineeringShortcutCard({
  id,
  title,
  titleUrdu,
  description,
  descriptionUrdu,
  href,
  icon: Icon,
  language,
}: EngineeringShortcutCardProps) {
  const isUrdu = language === "ur";
  const displayTitle = isUrdu ? titleUrdu : title;
  const displayDescription = isUrdu ? descriptionUrdu : description;

  return (
    <Link
      href={href}
      id={`shortcut-${id}`}
      data-shortcut-card="true"
      aria-label={`${displayTitle}: ${displayDescription}`}
      className={cn(
        "group relative flex items-start gap-3 p-3.5 sm:p-4 rounded-xl",
        "bg-white dark:bg-navy-900/90 border border-slate-200/90 dark:border-slate-800",
        "hover:border-orange-500/50 hover:bg-orange-50/40 dark:hover:bg-navy-800/80",
        "focus:outline-none focus:ring-2 focus:ring-orange-500/40 focus:border-orange-500",
        "shadow-2xs hover:shadow-xs transition-all duration-200 text-left min-h-[76px] cursor-pointer",
        isUrdu && "text-right flex-row-reverse"
      )}
    >
      <div
        className={cn(
          "w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0",
          "bg-orange-50 dark:bg-navy-800 text-orange-500 border border-orange-100 dark:border-navy-700",
          "group-hover:scale-105 group-hover:bg-orange-500 group-hover:text-white transition-all duration-200"
        )}
      >
        <Icon className="w-4 h-4" />
      </div>

      <div className="flex-1 min-w-0">
        <h4 className="text-xs sm:text-sm font-bold text-navy-900 dark:text-white group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors leading-tight truncate">
          {displayTitle}
        </h4>
        <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug mt-1 line-clamp-2">
          {displayDescription}
        </p>
      </div>
    </Link>
  );
}

