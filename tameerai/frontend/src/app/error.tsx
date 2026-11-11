"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, RefreshCw, Home, LayoutDashboard } from "lucide-react";
import TameerLogo from "@/components/brand/TameerLogo";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[TameerAI ErrorBoundary]:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-navy-950 flex flex-col items-center justify-center p-4 font-sans text-slate-900 dark:text-white">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="flex justify-center">
          <TameerLogo size="md" />
        </div>

        <div className="w-16 h-16 rounded-2xl bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 flex items-center justify-center mx-auto shadow-sm">
          <AlertTriangle className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <span className="text-xs font-black uppercase tracking-widest text-rose-600 dark:text-rose-400">
            System Execution Notice
          </span>
          <h1 className="text-2xl font-black text-navy-900 dark:text-white tracking-tight">
            Unexpected Workspace Error
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
            An unexpected error occurred while processing engineering calculations or rendering dashboard modules.
          </p>
          {error.digest && (
            <p className="text-[10px] font-mono text-slate-400">
              Error Digest: {error.digest}
            </p>
          )}
        </div>

        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={() => reset()}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 text-white shadow-sm transition-all"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Try Again</span>
          </button>
          <Link
            href="/dashboard"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-white dark:bg-navy-900 hover:bg-slate-100 dark:hover:bg-navy-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition-all shadow-2xs"
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Dashboard</span>
          </Link>
        </div>

        <div className="text-[11px] text-slate-400 pt-6 border-t border-slate-200 dark:border-slate-800">
          <span>TameerAI Construction Intelligence Platform</span>
        </div>
      </div>
    </div>
  );
}

