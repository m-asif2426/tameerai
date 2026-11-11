"use client";

import Link from "next/link";
import { ArrowLeft, Home, LayoutDashboard, Search, FileQuestion } from "lucide-react";
import TameerLogo from "@/components/brand/TameerLogo";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-navy-950 flex flex-col items-center justify-center p-4 font-sans text-slate-900 dark:text-white">
      <div className="max-w-md w-full text-center space-y-6">
        {/* Brand Logo */}
        <div className="flex justify-center">
          <TameerLogo size="md" />
        </div>

        {/* 404 Illustration / Icon */}
        <div className="w-20 h-20 rounded-3xl bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 flex items-center justify-center mx-auto shadow-sm">
          <FileQuestion className="w-10 h-10" />
        </div>

        {/* Message */}
        <div className="space-y-2">
          <span className="text-xs font-black uppercase tracking-widest text-orange-600 dark:text-orange-400">
            Error 404 · Resource Not Located
          </span>
          <h1 className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white tracking-tight">
            Page or Dossier Not Found
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
            The requested engineering blueprint, project workspace, or platform route does not exist or has been relocated under updated statutory revisions.
          </p>
          <p className="text-xs text-slate-400 font-urdu dir-rtl">
            مطلوبہ صفحہ، تعمیراتی منصوبہ یا دستاویز موجود نہیں ہے۔ براہ کرم ڈیش بورڈ پر واپس جائیں۔
          </p>
        </div>

        {/* Navigation Action Buttons */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            href="/dashboard"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-orange-500 hover:bg-orange-600 text-white shadow-sm transition-all"
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Go to Dashboard</span>
          </Link>
          <Link
            href="/"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-white dark:bg-navy-900 hover:bg-slate-100 dark:hover:bg-navy-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition-all shadow-2xs"
          >
            <Home className="w-4 h-4" />
            <span>Back to Home</span>
          </Link>
        </div>

        <div className="text-[11px] text-slate-400 pt-6 border-t border-slate-200 dark:border-slate-800">
          <span>TameerAI Construction Intelligence Platform</span>
        </div>
      </div>
    </div>
  );
}

