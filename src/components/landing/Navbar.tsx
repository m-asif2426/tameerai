"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useTheme } from "next-themes";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  Sun, Moon, Menu, X, Globe, ChevronDown, Zap
} from "lucide-react";
import { cn } from "@/lib/utils";
import TameerLogo from "@/components/brand/TameerLogo";

const navLinks = [
  { href: "#home", en: "Home", ur: "ہوم" },
  { href: "#features", en: "Features", ur: "خصوصیات" },
  { href: "#solutions", en: "Solutions", ur: "حل" },
  { href: "#how-it-works", en: "How it Works", ur: "کیسے کام کرتا ہے" },
  { href: "#about", en: "About", ur: "ہمارے بارے میں" },
];

export default function Navbar() {
  const { theme, setTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  const [mounted, setMounted] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setMounted(true);
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  if (!mounted) return null;

  return (
    <nav
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled
          ? "bg-white/95 dark:bg-navy-900/95 backdrop-blur-md shadow-sm border-b border-slate-100 dark:border-slate-800"
          : "bg-transparent"
      )}
    >
      <div className="container-custom">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center flex-shrink-0">
            <TameerLogo variant="full" size="sm" />
          </Link>

          {/* Center Nav Links */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="nav-link px-3 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                {t(link.en, link.ur)}
              </a>
            ))}
          </div>

          {/* Right Actions */}
          <div className="hidden md:flex items-center gap-2">
            {/* Language Toggle */}
            <button
              onClick={() => setLanguage(language === "en" ? "ur" : "en")}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium",
                "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800",
                "border border-slate-200 dark:border-slate-700 transition-all"
              )}
            >
              <Globe className="w-3.5 h-3.5" />
              <span>{language === "en" ? "اردو" : "English"}</span>
            </button>

            {/* Theme Toggle */}
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className={cn(
                "p-2 rounded-lg transition-all",
                "text-slate-600 dark:text-slate-400",
                "hover:bg-slate-100 dark:hover:bg-slate-800",
                "border border-slate-200 dark:border-slate-700"
              )}
              aria-label="Toggle theme"
            >
              {theme === "dark" ? (
                <Sun className="w-4 h-4" />
              ) : (
                <Moon className="w-4 h-4" />
              )}
            </button>

            <div className="w-px h-5 bg-slate-200 dark:bg-slate-700" />

            <Link
              href="/login"
              className="text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-navy-900 dark:hover:text-white px-3 py-2"
            >
              {t("Login", "لاگ ان")}
            </Link>
            <Link
              href="/signup"
              className="btn-primary text-sm px-4 py-2 rounded-lg"
            >
              {t("Get Started", "شروع کریں")}
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div className="md:hidden bg-white dark:bg-navy-900 border-t border-slate-100 dark:border-slate-800 px-4 py-4 space-y-1">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="block px-3 py-2.5 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg"
              onClick={() => setMobileOpen(false)}
            >
              {t(link.en, link.ur)}
            </a>
          ))}
          <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setLanguage(language === "en" ? "ur" : "en")}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700"
              >
                <Globe className="w-3.5 h-3.5" />
                {language === "en" ? "اردو" : "English"}
              </button>
              <button
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                className="p-2 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400"
              >
                {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
            </div>
            <Link href="/login" className="btn-secondary text-center text-sm py-2.5">
              {t("Login", "لاگ ان")}
            </Link>
            <Link href="/signup" className="btn-primary text-center text-sm py-2.5">
              {t("Get Started", "شروع کریں")}
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}
