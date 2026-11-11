"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useTheme } from "next-themes";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  Sun,
  Moon,
  Menu,
  X,
  Globe,
  ChevronDown,
  TrendingUp,
  ShieldAlert,
  Scale,
  FolderOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";
import TameerLogo from "@/components/brand/TameerLogo";

interface PlatformLink {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  enTitle: string;
  urTitle: string;
  enDesc: string;
  urDesc: string;
}

const platformItems: PlatformLink[] = [
  {
    href: "#rates",
    icon: TrendingUp,
    enTitle: "Material Rates",
    urTitle: "تعمیراتی میٹریل ریٹس",
    enDesc: "Canonical market benchmarks across Pakistan",
    urDesc: "پاکستان بھر کے مستند مارکیٹ ریٹس",
  },
  {
    href: "#safety",
    icon: ShieldAlert,
    enTitle: "Structural Safety",
    urTitle: "سٹرکچرل سیفٹی",
    enDesc: "Deterministic hazard assessment & directives",
    urDesc: "عمارتی خطرات کا فوری تکنیکی تجزیہ",
  },
  {
    href: "#regulations",
    icon: Scale,
    enTitle: "Regulations Explorer",
    urTitle: "عمارتی ضوابط ایکسپلورر",
    enDesc: "Bylaw discovery, clauses & legal search",
    urDesc: "بلڈنگ کوڈز، شقیں اور قانونی تلاش",
  },
  {
    href: "#features",
    icon: FolderOpen,
    enTitle: "Projects & BOQ",
    urTitle: "منصوبے اور بی او کیو",
    enDesc: "Engineering project workspaces and cost estimates",
    urDesc: "تعمیراتی منصوبے اور لاگت کا تخمینہ",
  },
];

export default function Navbar() {
  const { theme, setTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  const [mounted, setMounted] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [platformOpen, setPlatformOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);

    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setPlatformOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      window.removeEventListener("scroll", handleScroll);
      document.removeEventListener("mousedown", handleClickOutside);
    };
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
          {/* Geometric Architectural Logo */}
          <Link href="/" className="flex items-center flex-shrink-0">
            <TameerLogo variant="full" size="sm" />
          </Link>

          {/* Center Navigation Links: Home | Platform | How It Works | About Us | Contact Us */}
          <div className="hidden md:flex items-center gap-1">
            <a
              href="#home"
              className="nav-link px-3 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 text-sm font-medium"
            >
              {t("Home", "ہوم")}
            </a>

            {/* Platform Dropdown */}
            <div className="relative" ref={dropdownRef}>
              <button
                type="button"
                onClick={() => setPlatformOpen(!platformOpen)}
                className={cn(
                  "nav-link inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  platformOpen
                    ? "bg-slate-100 dark:bg-slate-800 text-orange-600 dark:text-orange-400"
                    : "hover:bg-slate-50 dark:hover:bg-slate-800"
                )}
                aria-expanded={platformOpen}
                aria-haspopup="true"
              >
                <span>{t("Platform", "پلیٹ فارم")}</span>
                <ChevronDown
                  className={cn(
                    "w-3.5 h-3.5 transition-transform duration-200",
                    platformOpen && "rotate-180 text-orange-500"
                  )}
                />
              </button>

              {platformOpen && (
                <div className="absolute top-full left-0 mt-2 w-80 bg-white dark:bg-navy-900 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800 p-2 z-50 animate-fade-in">
                  <div className="text-[10px] font-bold text-slate-400 dark:text-slate-500 px-3 py-1.5 uppercase tracking-wider">
                    {t("Platform Modules", "پلیٹ فارم ماڈیولز")}
                  </div>
                  <div className="space-y-1">
                    {platformItems.map((item) => {
                      const IconComponent = item.icon;
                      return (
                        <a
                          key={item.href}
                          href={item.href}
                          onClick={() => setPlatformOpen(false)}
                          className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/80 transition-colors group"
                        >
                          <div className="p-2 rounded-lg bg-orange-50 dark:bg-orange-950/40 text-orange-600 dark:text-orange-400 group-hover:scale-105 transition-transform">
                            <IconComponent className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors">
                              {t(item.enTitle, item.urTitle)}
                            </p>
                            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight mt-0.5">
                              {t(item.enDesc, item.urDesc)}
                            </p>
                          </div>
                        </a>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            <a
              href="#how-it-works"
              className="nav-link px-3 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 text-sm font-medium"
            >
              {t("How It Works", "طریقہ کار")}
            </a>
            <a
              href="#about"
              className="nav-link px-3 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 text-sm font-medium"
            >
              {t("About Us", "ہمارے بارے میں")}
            </a>
            <a
              href="#contact"
              className="nav-link px-3 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 text-sm font-medium"
            >
              {t("Contact Us", "رابطہ کریں")}
            </a>
          </div>

          {/* Right Controls & Auth Actions: Sign In | Get Started */}
          <div className="hidden md:flex items-center gap-2">
            {/* Bilingual Urdu / English Toggle */}
            <button
              onClick={() => setLanguage(language === "en" ? "ur" : "en")}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium",
                "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800",
                "border border-slate-200 dark:border-slate-700 transition-all"
              )}
              aria-label="Switch language"
            >
              <Globe className="w-3.5 h-3.5" />
              <span>{language === "en" ? "اردو" : "English"}</span>
            </button>

            {/* Dark / Light Theme Toggle */}
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
              {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            <div className="w-px h-5 bg-slate-200 dark:bg-slate-700 mx-1" />

            <Link
              href="/login"
              className="text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-orange-600 dark:hover:text-orange-400 px-3 py-2 transition-colors"
            >
              {t("Sign In", "سائن ان")}
            </Link>
            <Link
              href="/signup"
              className="btn-primary text-sm px-4 py-2 rounded-xl"
            >
              {t("Get Started", "شروع کریں")}
            </Link>
          </div>

          {/* Mobile Menu Toggle Button */}
          <button
            className="md:hidden p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Drawer */}
      {mobileOpen && (
        <div className="md:hidden bg-white dark:bg-navy-900 border-t border-slate-100 dark:border-slate-800 px-4 py-4 space-y-2 shadow-xl animate-fade-in">
          <a
            href="#home"
            className="block px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg"
            onClick={() => setMobileOpen(false)}
          >
            {t("Home", "ہوم")}
          </a>

          <div className="pt-2 pb-1 border-t border-slate-100 dark:border-slate-800">
            <p className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              {t("Platform Modules", "پلیٹ فارم ماڈیولز")}
            </p>
            {platformItems.map((item) => {
              const Icon = item.icon;
              return (
                <a
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-2.5 px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg"
                  onClick={() => setMobileOpen(false)}
                >
                  <Icon className="w-4 h-4 text-orange-500" />
                  <span>{t(item.enTitle, item.urTitle)}</span>
                </a>
              );
            })}
          </div>

          <a
            href="#how-it-works"
            className="block px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg"
            onClick={() => setMobileOpen(false)}
          >
            {t("How It Works", "طریقہ کار")}
          </a>
          <a
            href="#about"
            className="block px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg"
            onClick={() => setMobileOpen(false)}
          >
            {t("About Us", "ہمارے بارے میں")}
          </a>
          <a
            href="#contact"
            className="block px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg"
            onClick={() => setMobileOpen(false)}
          >
            {t("Contact Us", "رابطہ کریں")}
          </a>

          <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-col gap-2">
            <div className="flex items-center justify-between gap-2">
              <button
                onClick={() => setLanguage(language === "en" ? "ur" : "en")}
                className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
              >
                <Globe className="w-3.5 h-3.5" />
                <span>{language === "en" ? "اردو" : "English"}</span>
              </button>
              <button
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                className="p-2 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400"
                aria-label="Toggle theme"
              >
                {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
            </div>
            <Link
              href="/login"
              className="btn-secondary text-center text-sm py-2.5 rounded-xl"
              onClick={() => setMobileOpen(false)}
            >
              {t("Sign In", "سائن ان")}
            </Link>
            <Link
              href="/signup"
              className="btn-primary text-center text-sm py-2.5 rounded-xl"
              onClick={() => setMobileOpen(false)}
            >
              {t("Get Started", "شروع کریں")}
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}
