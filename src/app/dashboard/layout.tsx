"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  LayoutDashboard,
  FolderOpen,
  PlusCircle,
  MessageSquare,
  ShieldCheck,
  FileText,
  TrendingUp,
  BarChart3,
  Settings,
  LogOut,
  Sun,
  Moon,
  Globe,
  Menu,
  X,
  Bell,
  Search,
  ChevronDown,
  User,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import TameerLogo, { TameerIcon } from "@/components/brand/TameerLogo";

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, en: "Dashboard", ur: "ڈیش بورڈ" },
  { href: "/dashboard/projects", icon: FolderOpen, en: "Projects", ur: "منصوبے" },
  {
    href: "/dashboard/audit",
    icon: PlusCircle,
    en: "New Audit",
    ur: "نیا آڈٹ",
    badge: "AI",
    isAction: true,
  },
  { href: "/dashboard/ai-assistant", icon: MessageSquare, en: "AI Assistant", ur: "اے آئی اسسٹنٹ" },
  { href: "/dashboard/compliance", icon: ShieldCheck, en: "Compliance Check", ur: "تعمیل کی جانچ" },
  { href: "/dashboard/contracts", icon: FileText, en: "Contract Analyzer", ur: "معاہدہ تجزیہ کار" },
  { href: "/dashboard/costs", icon: TrendingUp, en: "Cost Intelligence", ur: "لاگت انٹیلی جنس" },
  { href: "/dashboard/reports", icon: BarChart3, en: "Reports", ur: "رپورٹس" },
  { href: "/dashboard/settings", icon: Settings, en: "Settings", ur: "ترتیبات" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const SidebarContent = () => (
    <div className="flex flex-col h-full bg-white dark:bg-navy-900 border-r border-slate-200/80 dark:border-slate-800">
      {/* Brand Logo Header */}
      <div className="flex items-center justify-between px-3.5 h-16 border-b border-slate-100 dark:border-slate-800/80">
        {sidebarOpen ? (
          <>
            <Link href="/dashboard" className="flex items-center">
              <TameerLogo variant="full" size="sm" />
            </Link>
            <button
              type="button"
              onClick={() => setSidebarOpen(false)}
              className="hidden lg:flex p-1.5 rounded-lg text-slate-400 hover:text-orange-500 hover:bg-orange-50 dark:hover:bg-slate-800 transition-colors"
              title={t("Collapse Sidebar", "سائیڈ بار بند کریں")}
              aria-label="Collapse Sidebar"
            >
              <Menu className="w-4 h-4" />
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="hidden lg:flex mx-auto p-1.5 rounded-lg text-slate-400 hover:text-orange-500 hover:bg-orange-50 dark:hover:bg-slate-800 transition-colors"
            title={t("Expand Sidebar", "سائیڈ بار کھولیں")}
            aria-label="Expand Sidebar"
          >
            <TameerIcon size={28} />
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            pathname === item.href ||
            (item.href.includes("?") && pathname === item.href.split("?")[0]);

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileSidebarOpen(false)}
              className={cn(
                "group flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all",
                isActive
                  ? "bg-orange-500/10 text-orange-600 dark:text-orange-400 font-bold shadow-xs border border-orange-500/20"
                  : "text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white hover:bg-slate-100/70 dark:hover:bg-slate-800/60",
                !sidebarOpen && "justify-center px-2",
                item.isAction &&
                  !isActive &&
                  "bg-orange-500 text-white hover:bg-orange-600 dark:text-white hover:text-white shadow-xs"
              )}
              title={!sidebarOpen ? t(item.en, item.ur) : undefined}
            >
              <Icon
                className={cn(
                  "w-4 h-4 flex-shrink-0 transition-transform group-hover:scale-110",
                  isActive
                    ? "text-orange-600 dark:text-orange-400"
                    : item.isAction
                    ? "text-white"
                    : "text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-200"
                )}
              />
              {sidebarOpen && (
                <span className="flex-1 truncate">{t(item.en, item.ur)}</span>
              )}
              {sidebarOpen && item.badge && !item.isAction && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-md bg-orange-100 dark:bg-orange-950 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-800">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* User Profile Footer: Aslam Bhai */}
      <div
        className={cn(
          "p-3 border-t border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-navy-950/40",
          !sidebarOpen && "px-2"
        )}
      >
        <div className={cn("flex items-center gap-3", !sidebarOpen && "justify-center")}>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 text-white font-black text-xs flex items-center justify-center flex-shrink-0 shadow-sm shadow-orange-500/20">
            AB
          </div>
          {sidebarOpen && (
            <div className="flex-1 min-w-0">
              <p className="text-xs font-bold text-navy-900 dark:text-white truncate">
                {t("Aslam Bhai", "اسلم بھائی")}
              </p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                {t("Senior Contractor", "سینئر ٹھیکیدار")}
              </p>
            </div>
          )}
          {sidebarOpen && (
            <Link
              href="/login"
              title={t("Logout", "لاگ آؤٹ")}
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </Link>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-navy-950 flex text-slate-900 dark:text-slate-100">
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          "hidden lg:flex flex-col flex-shrink-0 transition-all duration-300 z-20",
          sidebarOpen ? "w-60" : "w-16"
        )}
      >
        <SidebarContent />
      </aside>

      {/* Mobile Sidebar Overlay Drawer */}
      {mobileSidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="absolute inset-0 bg-navy-950/60 backdrop-blur-sm"
            onClick={() => setMobileSidebarOpen(false)}
          />
          <aside className="relative w-64 bg-white dark:bg-navy-900 flex flex-col shadow-2xl z-10 animate-slide-in-right">
            <button
              onClick={() => setMobileSidebarOpen(false)}
              className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label="Close menu"
            >
              <X className="w-5 h-5" />
            </button>
            <SidebarContent />
          </aside>
        </div>
      )}

      {/* Main App Container */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* ========================================================= */}
        {/* TOP BAR: Search, Language toggle, Theme toggle, Profile    */}
        {/* ========================================================= */}
        <header className="sticky top-0 z-30 bg-white/95 dark:bg-navy-900/95 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 px-4 lg:px-6 h-16 flex items-center justify-between gap-4 flex-shrink-0">
          {/* Left: Sidebar toggle + Global Search */}
          <div className="flex items-center gap-3 flex-1 max-w-xl">
            <button
              onClick={() => setMobileSidebarOpen(true)}
              className="lg:hidden p-2 rounded-xl text-slate-500 hover:text-navy-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label="Toggle navigation"
              title={t("Open mobile menu", "موبائل مینو کھولیں")}
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Search Input Bar */}
            <div className="relative w-full">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Search className="w-4 h-4" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t(
                  "Search projects, building codes (PBC 2021), contracts...",
                  "منصوبے، بلڈنگ کوڈز (PBC 2021) یا معاہدات تلاش کریں..."
                )}
                className="w-full pl-9 pr-12 py-2 rounded-xl text-xs bg-slate-100/80 dark:bg-navy-950 border border-transparent focus:border-orange-500/40 dark:focus:border-orange-500/40 text-navy-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-500/20 transition-all"
              />
              <div className="hidden sm:flex absolute inset-y-0 right-0 pr-2.5 items-center">
                <kbd className="px-1.5 py-0.5 text-[10px] font-semibold text-slate-400 bg-white dark:bg-navy-800 border border-slate-200 dark:border-slate-700 rounded shadow-2xs">
                  ⌘K
                </kbd>
              </div>
            </div>
          </div>

          {/* Right: Controls (Language, Theme, Notifications, Profile) */}
          <div className="flex items-center gap-2.5 flex-shrink-0">
            {/* Language toggle: English | اردو */}
            <button
              type="button"
              onClick={() => setLanguage(language === "en" ? "ur" : "en")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100/80 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 hover:border-orange-500/40 transition-all shadow-2xs"
              title="Toggle English / اردو"
            >
              <Globe className="w-3.5 h-3.5 text-orange-500" />
              <span>{language === "en" ? "اردو" : "English"}</span>
            </button>

            {/* Theme toggle: Light | Dark */}
            <button
              type="button"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="p-2 rounded-xl text-slate-600 dark:text-slate-400 bg-slate-100/80 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 hover:text-orange-500 dark:hover:text-orange-400 transition-colors shadow-2xs"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            {/* Notification Bell */}
            <button
              className="relative p-2 rounded-xl text-slate-600 dark:text-slate-400 bg-slate-100/80 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 hover:text-orange-500 transition-colors shadow-2xs"
              aria-label="Notifications"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-orange-500 rounded-full ring-2 ring-white dark:ring-navy-900" />
            </button>

            {/* Profile Dropdown / Badge */}
            <div className="flex items-center gap-2.5 pl-2 border-l border-slate-200 dark:border-slate-800">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 text-white font-black text-xs flex items-center justify-center shadow-xs">
                AB
              </div>
              <div className="hidden md:block text-left">
                <p className="text-xs font-bold text-navy-900 dark:text-white leading-none">
                  {t("Aslam Bhai", "اسلم بھائی")}
                </p>
                <p className="text-[10px] text-slate-400 mt-0.5 leading-none">
                  {t("Thekedar", "ٹھیکیدار")}
                </p>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content Body */}
        <main className="flex-1 overflow-auto p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
