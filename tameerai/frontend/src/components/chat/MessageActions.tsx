"use client";

import React, { useState } from "react";
import { Copy, Check, ThumbsUp, ThumbsDown, Share2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface MessageActionsProps {
  messageId: string;
  content: string;
  className?: string;
  language?: "en" | "ur";
  onFeedback?: (messageId: string, feedback: "up" | "down") => void;
}

export function MessageActions({
  messageId,
  content,
  className,
  language = "en",
  onFeedback,
}: MessageActionsProps) {
  const [copied, setCopied] = useState(false);
  const [feedbackState, setFeedbackState] = useState<"up" | "down" | null>(null);
  const isUrdu = language === "ur";

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFeedback = (type: "up" | "down") => {
    const next = feedbackState === type ? null : type;
    setFeedbackState(next);
    if (onFeedback && next) {
      onFeedback(messageId, next);
    }
  };

  return (
    <div
      data-testid="message-actions-toolbar"
      className={cn(
        "flex items-center gap-1 text-[11px] text-slate-400 dark:text-slate-500 pt-1",
        className
      )}
    >
      {/* Copy Response Button */}
      <button
        type="button"
        onClick={handleCopy}
        className={cn(
          "inline-flex items-center gap-1 px-2 py-1 rounded-md transition-colors",
          "hover:bg-slate-100 dark:hover:bg-navy-900 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200",
          copied && "text-emerald-600 dark:text-emerald-400 font-medium"
        )}
        title={isUrdu ? "مکمل جواب کاپی کریں" : "Copy response"}
        aria-label={isUrdu ? "مکمل جواب کاپی کریں" : "Copy response to clipboard"}
      >
        {copied ? (
          <>
            <Check className="w-3.5 h-3.5 text-emerald-500" />
            <span>{isUrdu ? "کاپی ہو گیا" : "Copied"}</span>
          </>
        ) : (
          <>
            <Copy className="w-3.5 h-3.5" />
            <span>{isUrdu ? "کاپی کریں" : "Copy"}</span>
          </>
        )}
      </button>

      {/* Helpful / Not Helpful Feedback Buttons */}
      <div className="flex items-center border-l border-slate-200 dark:border-slate-800 ml-1 pl-1">
        <button
          type="button"
          onClick={() => handleFeedback("up")}
          className={cn(
            "p-1 rounded-md transition-colors",
            "hover:bg-slate-100 dark:hover:bg-navy-900",
            feedbackState === "up"
              ? "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40"
              : "text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          )}
          title={isUrdu ? "مفید جواب" : "Helpful response"}
          aria-label={isUrdu ? "مفید جواب" : "Helpful response"}
        >
          <ThumbsUp className="w-3.5 h-3.5" />
        </button>

        <button
          type="button"
          onClick={() => handleFeedback("down")}
          className={cn(
            "p-1 rounded-md transition-colors",
            "hover:bg-slate-100 dark:hover:bg-navy-900",
            feedbackState === "down"
              ? "text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40"
              : "text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          )}
          title={isUrdu ? "غیر مفید جواب" : "Not helpful"}
          aria-label={isUrdu ? "غیر مفید جواب" : "Not helpful"}
        >
          <ThumbsDown className="w-3.5 h-3.5" />
        </button>
      </div>

      <span className="text-[10px] text-slate-400/80 ml-auto font-mono">
        {isUrdu ? "پی بی سی 2021 مطابقت" : "PBC 2021 Compliant"}
      </span>
    </div>
  );
}

