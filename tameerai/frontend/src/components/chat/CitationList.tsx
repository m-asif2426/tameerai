"use client";

import React, { useState } from "react";
import { BookOpen, Copy, Check, ExternalLink, ShieldCheck, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export interface CitationItem {
  code: string;
  clause: string;
  docId: string;
  page: number;
  year?: string | number;
  jurisdiction?: string;
  isVerified?: boolean;
}

export interface CitationListProps {
  citations: CitationItem[];
  className?: string;
  language?: "en" | "ur";
}

export function SourceAttribution({
  citation,
  language = "en",
}: {
  citation: CitationItem;
  language?: "en" | "ur";
}) {
  const [copied, setCopied] = useState(false);
  const isUrdu = language === "ur";

  const handleCopyCitation = () => {
    const text = `${citation.code} - ${citation.clause} [Doc ID: ${citation.docId}, Page ${citation.page}]`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      data-testid="source-attribution-item"
      className="p-3 rounded-xl bg-white dark:bg-navy-950 border border-slate-200 dark:border-slate-800 shadow-2xs space-y-2"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-6 h-6 rounded-md bg-orange-500/10 text-orange-600 dark:text-orange-400 flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-3.5 h-3.5" />
          </div>
          <span className="font-bold text-xs text-slate-900 dark:text-slate-100 font-mono truncate">
            {citation.code}
          </span>
        </div>

        {/* Verification Status Badge */}
        <span
          className={cn(
            "text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full flex-shrink-0 flex items-center gap-1",
            citation.isVerified
              ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300"
              : "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-300 border border-amber-300"
          )}
        >
          {citation.isVerified ? (
            <>
              <ShieldCheck className="w-2.5 h-2.5" />
              <span>{isUrdu ? "ماخذ سے تصدیق شدہ" : "Verified Source"}</span>
            </>
          ) : (
            <>
              <AlertCircle className="w-2.5 h-2.5" />
              <span>{isUrdu ? "غیر تصدیق شدہ — تصدیق ضروری ہے" : "UNVERIFIED - Subject to Source Verification"}</span>
            </>
          )}
        </span>
      </div>

      <div className="text-xs text-slate-700 dark:text-slate-300 pl-8">
        <div className="font-medium">{citation.clause}</div>
        <div className="flex items-center gap-3 text-[11px] text-slate-400 dark:text-slate-500 pt-1 font-mono">
          <span>Doc: {citation.docId}</span>
          <span>•</span>
          <span>Page {citation.page}</span>
          {citation.jurisdiction && (
            <>
              <span>•</span>
              <span>{citation.jurisdiction}</span>
            </>
          )}
        </div>
      </div>

      <div className="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] pl-8">
        <span className="text-[10px] text-slate-400 italic">
          {isUrdu ? "مستند بلڈنگ بائی لاز" : "Statutory reference citation"}
        </span>
        <button
          type="button"
          onClick={handleCopyCitation}
          className="inline-flex items-center gap-1 text-[10px] text-slate-500 hover:text-orange-500 transition-colors"
          title="Copy citation reference"
          aria-label="Copy citation"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-500" />
              <span className="text-emerald-600 font-medium">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy Ref</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}

export function CitationList({ citations, className, language = "en" }: CitationListProps) {
  const isUrdu = language === "ur";

  if (!citations || citations.length === 0) return null;

  return (
    <div
      data-testid="citation-list"
      className={cn(
        "my-3 pt-3 border-t border-slate-200/80 dark:border-slate-800 space-y-2.5",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700 dark:text-slate-300">
          <BookOpen className="w-3.5 h-3.5 text-orange-500" />
          <span>
            {isUrdu
              ? "ریگولیٹری حوالہ جات (ماخذ سے آزادانہ تصدیق ضروری ہے)"
              : "Regulatory References (Subject to Independent Verification)"}
          </span>
        </div>
        <span className="text-[10px] text-slate-400 font-mono">
          {citations.length} {citations.length === 1 ? "reference" : "references"}
        </span>
      </div>

      <div className="space-y-2">
        {citations.map((c, idx) => (
          <SourceAttribution key={idx} citation={c} language={language} />
        ))}
      </div>
    </div>
  );
}

