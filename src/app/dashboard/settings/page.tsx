"use client";

import { useState } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import { useTheme } from "next-themes";
import {
  User,
  Globe,
  Sun,
  Moon,
  Bell,
  ShieldCheck,
  Sparkles,
  Lock,
  Key,
  Smartphone,
  Laptop,
  Check,
  CheckCircle2,
  AlertTriangle,
  Building2,
  Save,
  FileText,
  Sliders,
  Scale,
  Coins,
  Shield,
  LogOut,
  MapPin,
  Mail,
  Phone,
  Camera,
  Bot,
} from "lucide-react";
import { cn } from "@/lib/utils";

// Settings Navigation Tabs
type SettingsSection =
  | "profile"
  | "language"
  | "theme"
  | "notifications"
  | "security"
  | "ai_preferences";

interface TabItem {
  id: SettingsSection;
  icon: typeof User;
  en: string;
  ur: string;
  descriptionEn: string;
  descriptionUr: string;
}

const SETTINGS_TABS: TabItem[] = [
  {
    id: "profile",
    icon: User,
    en: "Profile",
    ur: "پروفائل",
    descriptionEn: "Contractor identity, PEC licensing & company info",
    descriptionUr: "ٹھیکیدار شناخت، پی ای سی لائسنس اور کمپنی معلومات",
  },
  {
    id: "language",
    icon: Globe,
    en: "Language",
    ur: "زبان",
    descriptionEn: "Select English or Urdu bilingual interface",
    descriptionUr: "انگریزی یا اردو زبان کا انتخاب کریں",
  },
  {
    id: "theme",
    icon: Sun,
    en: "Theme",
    ur: "تھیم",
    descriptionEn: "Toggle Light or Dark architectural mode",
    descriptionUr: "لائٹ یا ڈارک موڈ تبدیل کریں",
  },
  {
    id: "notifications",
    icon: Bell,
    en: "Notifications",
    ur: "اطلاعات (Alerts)",
    descriptionEn: "Building code violations & cost spike alerts",
    descriptionUr: "بلڈنگ کوڈ نقائص اور میٹریل ریٹس کے الرٹس",
  },
  {
    id: "security",
    icon: ShieldCheck,
    en: "Account Security",
    ur: "اکاؤنٹ سیکیورٹی",
    descriptionEn: "Password, 2-Factor Authentication & active sessions",
    descriptionUr: "پاس ورڈ، 2-مرحلہ تصدیق اور فعال ڈیوائسز",
  },
  {
    id: "ai_preferences",
    icon: Sparkles,
    en: "AI Preferences",
    ur: "اے آئی ترجیحات",
    descriptionEn: "PBC 2021 enforcement strictness & FIDIC rules",
    descriptionUr: "پی بی سی 2021 اور فڈک معاہداتی ترجیحات",
  },
];

export default function SettingsPage() {
  const { t, language, setLanguage } = useLanguage();
  const { theme, setTheme } = useTheme();

  const [activeSection, setActiveSection] = useState<SettingsSection>("profile");
  const [saveToast, setSaveToast] = useState<string | null>(null);

  // Profile Form State
  const [profileData, setProfileData] = useState({
    fullName: "Aslam Bhai (Thekedar)",
    role: "Lead Contractor & Managing Partner",
    company: "Aslam Construction & Engineering Associates",
    pecNumber: "PEC/REG/CIVIL-44910",
    email: "aslam.thekedar@tameerai.pk",
    phone: "+92 300 8492011",
    city: "Lahore, Punjab (LDA Jurisdiction)",
    bio: "Specializing in commercial plaza structural framing, LDA compliance approvals, and FIDIC contractor administration in Lahore & Rawalpindi.",
  });

  // Notification Preferences State
  const [notifications, setNotifications] = useState({
    pbcViolations: true,
    fidicRisks: true,
    priceSpikes: true,
    weeklyDigest: false,
    whatsappAlerts: true,
  });

  // Security Form State
  const [securityData, setSecurityData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
    twoFactorEnabled: true,
  });

  // AI Preferences State
  const [aiSettings, setAiSettings] = useState({
    strictness: "strict", // 'strict' | 'consultative'
    fidicThreshold: "8", // '6' | '8' | '9'
    autoCitations: true,
    marketRegion: "lahore", // 'lahore' | 'karachi' | 'islamabad'
    aiTone: "professional", // 'professional' | 'practical' | 'legal'
  });

  const showToast = (message: string) => {
    setSaveToast(message);
    setTimeout(() => setSaveToast(null), 3000);
  };

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    showToast(
      language === "ur"
        ? "پروفائل کامیابی سے محفوظ ہوگئی!"
        : "Profile changes successfully saved!"
    );
  };

  const handleSaveSecurity = (e: React.FormEvent) => {
    e.preventDefault();
    setSecurityData((prev) => ({
      ...prev,
      currentPassword: "",
      newPassword: "",
      confirmPassword: "",
    }));
    showToast(
      language === "ur"
        ? "سیکیورٹی ترتیبات اور پاس ورڈ اپ ڈیٹ ہو گیا!"
        : "Security settings and password updated successfully!"
    );
  };

  const handleSaveAIPreferences = () => {
    showToast(
      language === "ur"
        ? "اے آئی آڈٹ ترجیحات اپ ڈیٹ ہو گئیں!"
        : "AI Audit preferences updated successfully!"
    );
  };

  return (
    <div className="space-y-6 pb-16 font-sans">
      {/* Toast Notification */}
      {saveToast && (
        <div className="fixed top-20 right-6 z-50 bg-emerald-600 text-white px-4 py-2.5 rounded-xl shadow-xl flex items-center gap-2 text-xs font-bold animate-in fade-in slide-in-from-top-4">
          <CheckCircle2 className="w-4 h-4" />
          <span>{saveToast}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20">
              {t("Account & Workspace Configuration", "اکاؤنٹ اور ورک اسپیس ترتیبات")}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white tracking-tight flex items-center gap-2.5">
            <Sliders className="w-6 h-6 text-orange-500" />
            <span>{t("Settings", "ترتیبات (Settings)")}</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {t(
              "Manage profile credentials, localization, visual theme, real-time alerts, account security, and AI construction parameters.",
              "اپنی پروفائل، زبان، تھیم، اطلاعات، سیکیورٹی اور اے آئی آڈٹ ترجیحات کو کنٹرول کریں۔"
            )}
          </p>
        </div>
      </div>

      {/* Layout Grid: Left Sidebar Tabs + Right Content Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Sidebar Navigation */}
        <div className="lg:col-span-4 xl:col-span-3">
          <div className="p-2 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-1">
            {SETTINGS_TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeSection === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveSection(tab.id)}
                  className={cn(
                    "w-full flex items-start gap-3 p-3 rounded-xl text-left transition-all group",
                    isActive
                      ? "bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 shadow-2xs"
                      : "text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-navy-950"
                  )}
                >
                  <div
                    className={cn(
                      "p-2 rounded-lg transition-colors flex-shrink-0 mt-0.5",
                      isActive
                        ? "bg-orange-500 text-white"
                        : "bg-slate-100 dark:bg-navy-950 text-slate-500 group-hover:text-navy-900 dark:group-hover:text-white"
                    )}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs sm:text-sm font-bold truncate">
                        {t(tab.en, tab.ur)}
                      </span>
                      {isActive && (
                        <span className="w-1.5 h-1.5 rounded-full bg-orange-500 flex-shrink-0" />
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 truncate mt-0.5">
                      {t(tab.descriptionEn, tab.descriptionUr)}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Quick Info Box */}
          <div className="mt-4 p-4 rounded-2xl bg-slate-50 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 text-xs space-y-2">
            <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300 font-bold">
              <Building2 className="w-4 h-4 text-orange-500" />
              <span>{t("TameerAI Enterprise Node", "تعمیر اے آئی انٹرپرائز")}</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              {t(
                "Version 2.4.0 · Connected to Pakistan Building Code (PBC 2021) Knowledge Engine.",
                "ورژن 2.4.0 · پاکستان بلڈنگ کوڈ (پی بی سی 2021) ڈیٹا بیس سے منسلک۔"
              )}
            </p>
          </div>
        </div>

        {/* Right Content Area */}
        <div className="lg:col-span-8 xl:col-span-9 space-y-6">
          {/* ========================================================================= */}
          {/* SECTION 1: PROFILE                                                        */}
          {/* ========================================================================= */}
          {activeSection === "profile" && (
            <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-6 animate-in fade-in duration-200">
              <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
                <h2 className="text-base sm:text-lg font-bold text-navy-900 dark:text-white flex items-center gap-2">
                  <User className="w-5 h-5 text-orange-500" />
                  <span>{t("Profile Information", "پروفائل معلومات")}</span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  {t(
                    "Update your personal details, Pakistan Engineering Council (PEC) registration, and company profile.",
                    "اپنا نام، پی ای سی رجسٹریشن نمبر، کمپنی اور رابطے کی تفصیلات اپ ڈیٹ کریں۔"
                  )}
                </p>
              </div>

              {/* Avatar & Header Badge */}
              <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4 p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800">
                <div className="relative group">
                  <div className="w-18 h-18 rounded-2xl bg-orange-500 text-white flex items-center justify-center font-black text-2xl shadow-md border-2 border-white dark:border-navy-900">
                    AB
                  </div>
                  <button
                    type="button"
                    title={t("Upload new photo", "تصویر تبدیل کریں")}
                    className="absolute -bottom-1.5 -right-1.5 p-1.5 rounded-full bg-navy-900 text-white dark:bg-white dark:text-navy-900 shadow-md hover:scale-105 transition-transform"
                  >
                    <Camera className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="text-center sm:text-left space-y-1 flex-1">
                  <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                    <h3 className="font-bold text-navy-900 dark:text-white text-base">
                      {profileData.fullName}
                    </h3>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                      {t("PEC Verified", "پی ای سی تصدیق شدہ")}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {profileData.role} · {profileData.company}
                  </p>
                  <p className="text-[11px] font-mono text-orange-600 dark:text-orange-400">
                    {profileData.pecNumber}
                  </p>
                </div>
              </div>

              {/* Form Fields */}
              <form onSubmit={handleSaveProfile} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                      {t("Full Name", "پورا نام")}
                    </label>
                    <div className="relative">
                      <User className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        value={profileData.fullName}
                        onChange={(e) =>
                          setProfileData({ ...profileData, fullName: e.target.value })
                        }
                        className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-1 focus:ring-orange-500 text-navy-900 dark:text-white"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                      {t("Professional Role / Designation", "پیشہ ورانہ عہدہ")}
                    </label>
                    <input
                      type="text"
                      value={profileData.role}
                      onChange={(e) =>
                        setProfileData({ ...profileData, role: e.target.value })
                      }
                      className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-1 focus:ring-orange-500 text-navy-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                      {t("Company / Firm Name", "کمپنی کا نام")}
                    </label>
                    <div className="relative">
                      <Building2 className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        value={profileData.company}
                        onChange={(e) =>
                          setProfileData({ ...profileData, company: e.target.value })
                        }
                        className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-1 focus:ring-orange-500 text-navy-900 dark:text-white"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                      {t("PEC Registration Number", "پی ای سی رجسٹریشن نمبر")}
                    </label>
                    <input
                      type="text"
                      value={profileData.pecNumber}
                      onChange={(e) =>
                        setProfileData({ ...profileData, pecNumber: e.target.value })
                      }
                      className="w-full px-3 py-2 text-xs font-mono bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-1 focus:ring-orange-500 text-navy-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                      {t("Official Email Address", "سرکاری ای میل ایڈریس")}
                    </label>
                    <div className="relative">
                      <Mail className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        type="email"
                        value={profileData.email}
                        onChange={(e) =>
                          setProfileData({ ...profileData, email: e.target.value })
                        }
                        className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-1 focus:ring-orange-500 text-navy-900 dark:text-white"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                      {t("Phone Number (WhatsApp Alerts)", "فون نمبر (واٹس ایپ الرٹس)")}
                    </label>
                    <div className="relative">
                      <Phone className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        value={profileData.phone}
                        onChange={(e) =>
                          setProfileData({ ...profileData, phone: e.target.value })
                        }
                        className="w-full pl-9 pr-3 py-2 text-xs font-mono bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-1 focus:ring-orange-500 text-navy-900 dark:text-white"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                    {t("Primary Construction Jurisdiction", "بنیادی تعمیراتی دائرہ اختیار")}
                  </label>
                  <div className="relative">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={profileData.city}
                      onChange={(e) =>
                        setProfileData({ ...profileData, city: e.target.value })
                      }
                      className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-1 focus:ring-orange-500 text-navy-900 dark:text-white"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                    {t("Professional Summary / Contractor Bio", "مختصر تعارف / بائیو")}
                  </label>
                  <textarea
                    rows={3}
                    value={profileData.bio}
                    onChange={(e) =>
                      setProfileData({ ...profileData, bio: e.target.value })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-1 focus:ring-orange-500 text-navy-900 dark:text-white resize-none"
                  />
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-orange-500 hover:bg-orange-600 shadow-sm shadow-orange-500/20 active:scale-95 transition-all"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>{t("Save Changes", "تبدیلیاں محفوظ کریں")}</span>
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* ========================================================================= */}
          {/* SECTION 2: LANGUAGE                                                       */}
          {/* ========================================================================= */}
          {activeSection === "language" && (
            <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-6 animate-in fade-in duration-200">
              <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
                <h2 className="text-base sm:text-lg font-bold text-navy-900 dark:text-white flex items-center gap-2">
                  <Globe className="w-5 h-5 text-orange-500" />
                  <span>{t("Language Settings", "زبان کی ترتیبات (Language)")}</span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  {t(
                    "Choose between English and Urdu. Switching language immediately reconfigures all audit reports, AI assistant conversations, and contract clauses.",
                    "انگریزی یا اردو کا انتخاب کریں۔ زبان تبدیل کرنے پر تمام آڈٹ رپورٹس، چیٹ اور تجاویز فوری ترجمہ ہو جائیں گی۔"
                  )}
                </p>
              </div>

              {/* Cards Grid: English & Urdu */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* English Option */}
                <button
                  type="button"
                  onClick={() => {
                    setLanguage("en");
                    showToast("Switched language to English");
                  }}
                  className={cn(
                    "p-5 rounded-2xl border-2 text-left transition-all flex flex-col justify-between space-y-4 group",
                    language === "en"
                      ? "border-orange-500 bg-orange-50/50 dark:bg-orange-950/20 shadow-xs"
                      : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-slate-50/50 dark:bg-navy-950"
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-orange-500/10 text-orange-600 dark:text-orange-400 flex items-center justify-center font-bold text-sm">
                        EN
                      </div>
                      <div>
                        <h3 className="font-bold text-sm text-navy-900 dark:text-white">
                          English
                        </h3>
                        <p className="text-[11px] text-slate-400">
                          International Engineering Standard
                        </p>
                      </div>
                    </div>
                    {language === "en" ? (
                      <div className="w-5 h-5 rounded-full bg-orange-500 text-white flex items-center justify-center">
                        <Check className="w-3 h-3 stroke-[3]" />
                      </div>
                    ) : (
                      <div className="w-5 h-5 rounded-full border-2 border-slate-300 dark:border-slate-700" />
                    )}
                  </div>

                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    Uses official Pakistan Building Code (PBC 2021) English statutory terms, FIDIC Red Book standard legal terminology, and international BOQ formats.
                  </p>

                  <div className="p-2.5 rounded-xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 text-[11px] font-mono text-slate-500">
                    Preview: "Stairway width deficit: 3.5 ft vs 4.0 ft required."
                  </div>
                </button>

                {/* Urdu Option */}
                <button
                  type="button"
                  onClick={() => {
                    setLanguage("ur");
                    showToast("اردو زبان منتخب کر لی گئی ہے");
                  }}
                  className={cn(
                    "p-5 rounded-2xl border-2 text-left transition-all flex flex-col justify-between space-y-4 group",
                    language === "ur"
                      ? "border-orange-500 bg-orange-50/50 dark:bg-orange-950/20 shadow-xs"
                      : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-slate-50/50 dark:bg-navy-950"
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-orange-500/10 text-orange-600 dark:text-orange-400 flex items-center justify-center font-bold text-sm font-serif">
                        اردو
                      </div>
                      <div>
                        <h3 className="font-bold text-sm text-navy-900 dark:text-white font-serif">
                          اردو (Urdu)
                        </h3>
                        <p className="text-[11px] text-slate-400 font-serif">
                          قومی زبان اور مقامی اصطلاحات
                        </p>
                      </div>
                    </div>
                    {language === "ur" ? (
                      <div className="w-5 h-5 rounded-full bg-orange-500 text-white flex items-center justify-center">
                        <Check className="w-3 h-3 stroke-[3]" />
                      </div>
                    ) : (
                      <div className="w-5 h-5 rounded-full border-2 border-slate-300 dark:border-slate-700" />
                    )}
                  </div>

                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-serif">
                    مقامی ٹھیکیداروں، کلائنٹس اور انجینئرز کے لیے آسان اردو۔ بلڈنگ کوڈ کے نقائص، قانونی معاہدات اور سیمنٹ و سریے کے روزانہ مارکیٹ ریٹس اردو میں دیکھیں۔
                  </p>

                  <div className="p-2.5 rounded-xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 text-[11px] font-serif text-slate-500">
                    نمونہ: "سیڑھیوں کی چوڑائی میں نقص: مطلوبہ 4.0 فٹ، موجودہ 3.5 فٹ۔"
                  </div>
                </button>
              </div>

              {/* Status banner */}
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-700 dark:text-emerald-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>
                  {language === "en"
                    ? "Active Interface: English (LTR alignment active)"
                    : "فعال انٹرفیس: اردو (دائیں سے بائیں سائیڈ فعال ہے)"}
                </span>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* SECTION 3: THEME                                                          */}
          {/* ========================================================================= */}
          {activeSection === "theme" && (
            <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-6 animate-in fade-in duration-200">
              <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
                <h2 className="text-base sm:text-lg font-bold text-navy-900 dark:text-white flex items-center gap-2">
                  <Sun className="w-5 h-5 text-orange-500" />
                  <span>{t("Theme Preferences", "تھیم کی ترجیحات (Theme)")}</span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  {t(
                    "Switch between high-contrast Light mode (for direct sunlight on construction sites) and deep Dark mode (for blueprint & contract reviews).",
                    "تعمیراتی سائٹ کے لیے روشن لائٹ موڈ یا رات کے وقت بلو پرنٹ دیکھنے کے لیے ڈارک موڈ منتخب کریں۔"
                  )}
                </p>
              </div>

              {/* Cards Grid: Light & Dark */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Light Theme */}
                <button
                  type="button"
                  onClick={() => {
                    setTheme("light");
                    showToast("Switched to Light Mode");
                  }}
                  className={cn(
                    "p-5 rounded-2xl border-2 text-left transition-all flex flex-col justify-between space-y-4 group",
                    theme === "light"
                      ? "border-orange-500 bg-orange-50/40 shadow-xs"
                      : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-slate-50/50 dark:bg-navy-950"
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-600 flex items-center justify-center font-bold">
                        <Sun className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="font-bold text-sm text-slate-900">
                          {t("Light Mode", "روشن موڈ (Light)")}
                        </h3>
                        <p className="text-[11px] text-slate-500">
                          High daylight visibility
                        </p>
                      </div>
                    </div>
                    {theme === "light" ? (
                      <div className="w-5 h-5 rounded-full bg-orange-500 text-white flex items-center justify-center">
                        <Check className="w-3 h-3 stroke-[3]" />
                      </div>
                    ) : (
                      <div className="w-5 h-5 rounded-full border-2 border-slate-300" />
                    )}
                  </div>

                  {/* Visual mockup snippet */}
                  <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-2">
                    <div className="flex items-center justify-between text-[10px] text-slate-600">
                      <span className="font-bold">PBC 2021 Audit</span>
                      <span className="text-emerald-600 font-bold">92% PASS</span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-orange-500 w-3/4 rounded-full" />
                    </div>
                  </div>

                  <p className="text-xs text-slate-500">
                    {t(
                      "Crisp white cards, clean borders, ideal for outdoor iPad site inspections.",
                      "سائٹ پر سورج کی روشنی میں اسکرین دیکھنے کے لیے بہترین انتخاب۔"
                    )}
                  </p>
                </button>

                {/* Dark Theme */}
                <button
                  type="button"
                  onClick={() => {
                    setTheme("dark");
                    showToast("Switched to Dark Mode");
                  }}
                  className={cn(
                    "p-5 rounded-2xl border-2 text-left transition-all flex flex-col justify-between space-y-4 group",
                    theme === "dark"
                      ? "border-orange-500 bg-navy-950/80 shadow-xs"
                      : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-slate-50/50 dark:bg-navy-950"
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center font-bold">
                        <Moon className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="font-bold text-sm text-navy-900 dark:text-white">
                          {t("Dark Mode", "تاریک موڈ (Dark)")}
                        </h3>
                        <p className="text-[11px] text-slate-400">
                          Reduced eye strain for CAD analysis
                        </p>
                      </div>
                    </div>
                    {theme === "dark" ? (
                      <div className="w-5 h-5 rounded-full bg-orange-500 text-white flex items-center justify-center">
                        <Check className="w-3 h-3 stroke-[3]" />
                      </div>
                    ) : (
                      <div className="w-5 h-5 rounded-full border-2 border-slate-700" />
                    )}
                  </div>

                  {/* Visual mockup snippet */}
                  <div className="p-3 rounded-xl bg-navy-900 border border-slate-800 shadow-2xs space-y-2">
                    <div className="flex items-center justify-between text-[10px] text-slate-300">
                      <span className="font-bold">PBC 2021 Audit</span>
                      <span className="text-emerald-400 font-bold">92% PASS</span>
                    </div>
                    <div className="h-1.5 w-full bg-navy-950 rounded-full overflow-hidden">
                      <div className="h-full bg-orange-500 w-3/4 rounded-full" />
                    </div>
                  </div>

                  <p className="text-xs text-slate-400">
                    {t(
                      "Deep Navy palette inspired by architectural drafting consoles.",
                      "آفس میں طویل دیر تک معاہدات اور ڈرائنگز کا تجزیہ کرنے کے لیے موزوں۔"
                    )}
                  </p>
                </button>
              </div>

              {/* Status Banner */}
              <div className="p-3 rounded-xl bg-slate-100 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-300 flex items-center justify-between">
                <span>{t("Active Theme State:", "فعال تھیم:")}</span>
                <strong className="text-orange-600 dark:text-orange-400 capitalize font-mono">
                  {theme || "light"}
                </strong>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* SECTION 4: NOTIFICATIONS                                                  */}
          {/* ========================================================================= */}
          {activeSection === "notifications" && (
            <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-6 animate-in fade-in duration-200">
              <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
                <h2 className="text-base sm:text-lg font-bold text-navy-900 dark:text-white flex items-center gap-2">
                  <Bell className="w-5 h-5 text-orange-500" />
                  <span>{t("Notifications & Alerts", "اطلاعات اور الرٹس (Notifications)")}</span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  {t(
                    "Configure automated construction alerts for critical building code violations, FIDIC legal disputes, and commodity price spikes.",
                    "بلڈنگ کوڈ کی خلاف ورزیوں، معاہداتی خطرات اور سریے و سیمنٹ کی قیمتوں میں اضافے کے فوری الرٹس سیٹ کریں۔"
                  )}
                </p>
              </div>

              {/* Switches List */}
              <div className="space-y-4">
                {/* Notification Item 1: PBC Code Violation */}
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 flex items-start justify-between gap-4">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-orange-500" />
                      <h4 className="text-xs sm:text-sm font-bold text-navy-900 dark:text-white">
                        {t("Critical PBC 2021 Code Violations", "پی بی سی 2021 ضوابط کی خلاف ورزی")}
                      </h4>
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                      {t(
                        "Instant alert when architectural plan check detects egress deficiency, missing fire exit, or structural setback failure.",
                        "جب بھی ڈرائنگ میں سیڑھی کی چوڑائی یا فائر سیفٹی کا نقص نکلے تو فوری اطلاع دی جائے۔"
                      )}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setNotifications((prev) => ({
                        ...prev,
                        pbcViolations: !prev.pbcViolations,
                      }));
                      showToast("Updated PBC alerts preference");
                    }}
                    className={cn(
                      "relative w-11 h-6 rounded-full transition-colors flex-shrink-0 cursor-pointer",
                      notifications.pbcViolations ? "bg-orange-500" : "bg-slate-300 dark:bg-slate-700"
                    )}
                  >
                    <span
                      className={cn(
                        "absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow-xs",
                        notifications.pbcViolations ? "left-5.5" : "left-0.5"
                      )}
                    />
                  </button>
                </div>

                {/* Notification Item 2: FIDIC Contract Risks */}
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 flex items-start justify-between gap-4">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <Scale className="w-4 h-4 text-blue-500" />
                      <h4 className="text-xs sm:text-sm font-bold text-navy-900 dark:text-white">
                        {t("FIDIC Contract High-Risk Alerts", "فڈک معاہداتی خطرات کا الرٹ")}
                      </h4>
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                      {t(
                        "Notification when AI contract analyzer spots uncapped liquidated damages (>10%) or unfair termination clauses.",
                        "جب بھی معاہدے میں غیر منصفانہ جرمانہ یا بلا معاوضہ منسوخی کی شق سامنے آئے۔"
                      )}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setNotifications((prev) => ({
                        ...prev,
                        fidicRisks: !prev.fidicRisks,
                      }));
                      showToast("Updated contract alerts preference");
                    }}
                    className={cn(
                      "relative w-11 h-6 rounded-full transition-colors flex-shrink-0 cursor-pointer",
                      notifications.fidicRisks ? "bg-orange-500" : "bg-slate-300 dark:bg-slate-700"
                    )}
                  >
                    <span
                      className={cn(
                        "absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow-xs",
                        notifications.fidicRisks ? "left-5.5" : "left-0.5"
                      )}
                    />
                  </button>
                </div>

                {/* Notification Item 3: Material Price Spikes */}
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 flex items-start justify-between gap-4">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <Coins className="w-4 h-4 text-emerald-500" />
                      <h4 className="text-xs sm:text-sm font-bold text-navy-900 dark:text-white">
                        {t("Material Price Spikes (>3% in 24h)", "مٹیریل کی قیمت میں اضافہ (>3%)")}
                      </h4>
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                      {t(
                        "Daily radar notification when Grade-60 steel rebar, cement, or brick rates spike significantly in Lahore or Karachi.",
                        "سیمنٹ اور سریا کی قیمتوں میں غیر معمولی اضافے کی فوری اطلاع۔"
                      )}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setNotifications((prev) => ({
                        ...prev,
                        priceSpikes: !prev.priceSpikes,
                      }));
                      showToast("Updated commodity alerts preference");
                    }}
                    className={cn(
                      "relative w-11 h-6 rounded-full transition-colors flex-shrink-0 cursor-pointer",
                      notifications.priceSpikes ? "bg-orange-500" : "bg-slate-300 dark:bg-slate-700"
                    )}
                  >
                    <span
                      className={cn(
                        "absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow-xs",
                        notifications.priceSpikes ? "left-5.5" : "left-0.5"
                      )}
                    />
                  </button>
                </div>

                {/* Notification Item 4: WhatsApp Direct Alerts */}
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 flex items-start justify-between gap-4">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <Smartphone className="w-4 h-4 text-emerald-600" />
                      <h4 className="text-xs sm:text-sm font-bold text-navy-900 dark:text-white">
                        {t("WhatsApp Direct Instant Dispatch", "براہ راست واٹس ایپ الرٹس")}
                      </h4>
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                      {t(
                        "Deliver critical audit summaries directly to Aslam Bhai's registered WhatsApp (+92 300 8492011).",
                        "رجسٹرڈ موبائل نمبر پر پی ڈی ایف سمری اور الرٹس واٹس ایپ کے ذریعے وصول کریں۔"
                      )}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setNotifications((prev) => ({
                        ...prev,
                        whatsappAlerts: !prev.whatsappAlerts,
                      }));
                      showToast("Updated WhatsApp dispatch preference");
                    }}
                    className={cn(
                      "relative w-11 h-6 rounded-full transition-colors flex-shrink-0 cursor-pointer",
                      notifications.whatsappAlerts ? "bg-orange-500" : "bg-slate-300 dark:bg-slate-700"
                    )}
                  >
                    <span
                      className={cn(
                        "absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow-xs",
                        notifications.whatsappAlerts ? "left-5.5" : "left-0.5"
                      )}
                    />
                  </button>
                </div>

                {/* Notification Item 5: Weekly Digest */}
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 flex items-start justify-between gap-4">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-purple-500" />
                      <h4 className="text-xs sm:text-sm font-bold text-navy-900 dark:text-white">
                        {t("Monday Executive Dossier Digest", "ہفتہ وار سمری رپورٹ")}
                      </h4>
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                      {t(
                        "Receive an email briefing summarizing all active site inspections every Monday morning at 8:00 AM PKT.",
                        "ہر پیر کی صبح تمام جاری منصوبوں کی جامع خلاصہ ای میل حاصل کریں۔"
                      )}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setNotifications((prev) => ({
                        ...prev,
                        weeklyDigest: !prev.weeklyDigest,
                      }));
                      showToast("Updated weekly digest preference");
                    }}
                    className={cn(
                      "relative w-11 h-6 rounded-full transition-colors flex-shrink-0 cursor-pointer",
                      notifications.weeklyDigest ? "bg-orange-500" : "bg-slate-300 dark:bg-slate-700"
                    )}
                  >
                    <span
                      className={cn(
                        "absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow-xs",
                        notifications.weeklyDigest ? "left-5.5" : "left-0.5"
                      )}
                    />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* SECTION 5: ACCOUNT SECURITY                                               */}
          {/* ========================================================================= */}
          {activeSection === "security" && (
            <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-6 animate-in fade-in duration-200">
              <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
                <h2 className="text-base sm:text-lg font-bold text-navy-900 dark:text-white flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-orange-500" />
                  <span>{t("Account Security", "اکاؤنٹ سیکیورٹی (Account Security)")}</span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  {t(
                    "Manage your master password, 2-factor authentication, and monitor active logged-in construction devices.",
                    "اپنا پاس ورڈ تبدیل کریں، 2-مرحلہ تصدیق فعال کریں اور لاگ ان شدہ ڈیوائسز چیک کریں۔"
                  )}
                </p>
              </div>

              {/* Two-Factor Authentication Card */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Smartphone className="w-4 h-4 text-emerald-600" />
                    <h3 className="font-bold text-xs sm:text-sm text-navy-900 dark:text-white">
                      {t("Two-Factor Authentication (2FA)", "دو مرحلہ تصدیق (2FA)")}
                    </h3>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-black uppercase bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
                      {securityData.twoFactorEnabled ? t("Active", "فعال") : t("Disabled", "غیر فعال")}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    {t(
                      "Secure OTP code sent via SMS to +92 300 8492011 on every new login attempt.",
                      "ہر نئے لاگ ان پر آپ کے رجسٹرڈ نمبر پر تصدیقی او ٹی پی کوڈ بھیجا جائے گا۔"
                    )}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setSecurityData((prev) => ({
                      ...prev,
                      twoFactorEnabled: !prev.twoFactorEnabled,
                    }));
                    showToast(
                      securityData.twoFactorEnabled
                        ? "2FA has been disabled"
                        : "2FA has been enabled with SMS OTP"
                    );
                  }}
                  className={cn(
                    "px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all",
                    securityData.twoFactorEnabled
                      ? "bg-slate-200 dark:bg-navy-800 text-slate-700 dark:text-slate-200 hover:bg-slate-300"
                      : "bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs"
                  )}
                >
                  {securityData.twoFactorEnabled
                    ? t("Disable 2FA", "2FA بند کریں")
                    : t("Enable 2FA", "2FA فعال کریں")}
                </button>
              </div>

              {/* Password Change Form */}
              <form onSubmit={handleSaveSecurity} className="space-y-4">
                <h3 className="font-bold text-xs sm:text-sm text-navy-900 dark:text-white flex items-center gap-2">
                  <Key className="w-4 h-4 text-orange-500" />
                  <span>{t("Change Password", "پاس ورڈ تبدیل کریں")}</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                      {t("Current Password", "موجودہ پاس ورڈ")}
                    </label>
                    <div className="relative">
                      <Lock className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        type="password"
                        value={securityData.currentPassword}
                        onChange={(e) =>
                          setSecurityData({
                            ...securityData,
                            currentPassword: e.target.value,
                          })
                        }
                        placeholder="••••••••••••"
                        className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-1 focus:ring-orange-500 text-navy-900 dark:text-white"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                      {t("New Password", "نیا پاس ورڈ")}
                    </label>
                    <div className="relative">
                      <Lock className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        type="password"
                        value={securityData.newPassword}
                        onChange={(e) =>
                          setSecurityData({
                            ...securityData,
                            newPassword: e.target.value,
                          })
                        }
                        placeholder="••••••••••••"
                        className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-1 focus:ring-orange-500 text-navy-900 dark:text-white"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                      {t("Confirm New Password", "نئے پاس ورڈ کی تصدیق")}
                    </label>
                    <div className="relative">
                      <Lock className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        type="password"
                        value={securityData.confirmPassword}
                        onChange={(e) =>
                          setSecurityData({
                            ...securityData,
                            confirmPassword: e.target.value,
                          })
                        }
                        placeholder="••••••••••••"
                        className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-1 focus:ring-orange-500 text-navy-900 dark:text-white"
                        required
                      />
                    </div>
                  </div>
                </div>

                <div className="flex justify-end pt-1">
                  <button
                    type="submit"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold text-white bg-orange-500 hover:bg-orange-600 shadow-sm shadow-orange-500/20 transition-all"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>{t("Update Password", "پاس ورڈ اپ ڈیٹ کریں")}</span>
                  </button>
                </div>
              </form>

              {/* Active Sessions List */}
              <div className="space-y-3 pt-2 border-t border-slate-100 dark:border-slate-800">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-xs sm:text-sm text-navy-900 dark:text-white flex items-center gap-2">
                    <Laptop className="w-4 h-4 text-slate-500" />
                    <span>{t("Active Logged-in Devices", "لاگ ان شدہ ڈیوائسز")}</span>
                  </h3>
                  <button
                    type="button"
                    onClick={() => showToast("Terminated all other active sessions")}
                    className="text-[11px] font-bold text-rose-600 dark:text-rose-400 hover:underline"
                  >
                    {t("Log out other sessions", "دیگر تمام ڈیوائسز لاگ آؤٹ کریں")}
                  </button>
                </div>

                <div className="space-y-2">
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-3">
                      <Laptop className="w-4 h-4 text-emerald-500" />
                      <div>
                        <div className="font-bold text-navy-900 dark:text-white">
                          Chrome 128 on Windows 11 (Lahore, Pakistan)
                        </div>
                        <div className="text-[11px] text-slate-400">
                          IP: 182.185.120.45 · {t("Current Active Session", "موجودہ فعال سیشن")}
                        </div>
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600">
                      {t("This Device", "یہ ڈیوائس")}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-3">
                      <Smartphone className="w-4 h-4 text-slate-400" />
                      <div>
                        <div className="font-bold text-navy-900 dark:text-white">
                          TameerAI App on iPhone 15 Pro (DHA Lahore Site)
                        </div>
                        <div className="text-[11px] text-slate-400">
                          Last active: 2 hours ago
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => showToast("Logged out mobile session")}
                      className="text-[11px] text-slate-400 hover:text-rose-600 font-semibold"
                    >
                      {t("Revoke", "منسوخ")}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* SECTION 6: AI PREFERENCES                                                 */}
          {/* ========================================================================= */}
          {activeSection === "ai_preferences" && (
            <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs space-y-6 animate-in fade-in duration-200">
              <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
                <h2 className="text-base sm:text-lg font-bold text-navy-900 dark:text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-orange-500" />
                  <span>{t("AI Construction Audit Preferences", "اے آئی آڈٹ ترجیحات (AI Preferences)")}</span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  {t(
                    "Calibrate the AI engine's building code strictness, FIDIC contract sensitivity, regional market synchronization, and citation rigor.",
                    "اے آئی انجن کے بلڈنگ کوڈ چیکنگ کا طریقہ کار اور کنٹریکٹ رسک کی حساسیت مقرر کریں۔"
                  )}
                </p>
              </div>

              <div className="space-y-5">
                {/* 1. PBC 2021 Strictness */}
                <div className="space-y-2">
                  <label className="block text-xs font-bold text-navy-900 dark:text-white">
                    {t("PBC 2021 Compliance Engine Enforcement", "پی بی سی 2021 تعمیل کی سختی")}
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setAiSettings({ ...aiSettings, strictness: "strict" })}
                      className={cn(
                        "p-4 rounded-xl border-2 text-left transition-all",
                        aiSettings.strictness === "strict"
                          ? "border-orange-500 bg-orange-50/50 dark:bg-orange-950/20"
                          : "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-navy-950"
                      )}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <strong className="text-xs font-bold text-navy-900 dark:text-white">
                          {t("Strict Mandatory Enforcement", "سخت قانونی عملدرآمد (Strict)")}
                        </strong>
                        {aiSettings.strictness === "strict" && (
                          <Check className="w-3.5 h-3.5 text-orange-500" />
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400">
                        Zero tolerance for egress deficits (e.g., flag any staircase under 4.0 ft as critical failure).
                      </p>
                    </button>

                    <button
                      type="button"
                      onClick={() => setAiSettings({ ...aiSettings, strictness: "consultative" })}
                      className={cn(
                        "p-4 rounded-xl border-2 text-left transition-all",
                        aiSettings.strictness === "consultative"
                          ? "border-orange-500 bg-orange-50/50 dark:bg-orange-950/20"
                          : "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-navy-950"
                      )}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <strong className="text-xs font-bold text-navy-900 dark:text-white">
                          {t("Consultative Advisory", "مشاورتی جائزہ (Consultative)")}
                        </strong>
                        {aiSettings.strictness === "consultative" && (
                          <Check className="w-3.5 h-3.5 text-orange-500" />
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400">
                        Offers practical contractor workarounds and engineering variance alternatives.
                      </p>
                    </button>
                  </div>
                </div>

                {/* 2. FIDIC Risk Sensitivity */}
                <div className="space-y-2">
                  <label className="block text-xs font-bold text-navy-900 dark:text-white">
                    {t("FIDIC Contract Risk Sensitivity Threshold", "فڈک معاہداتی خطرہ تھریش ہولڈ")}
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { val: "6", label: "Conservative (6/10+)", desc: "Flag minor clauses" },
                      { val: "8", label: "Balanced (8/10+)", desc: "Standard FIDIC review" },
                      { val: "9", label: "Critical Only (9/10+)", desc: "Severe legal exposure" },
                    ].map((item) => (
                      <button
                        key={item.val}
                        type="button"
                        onClick={() =>
                          setAiSettings({ ...aiSettings, fidicThreshold: item.val })
                        }
                        className={cn(
                          "p-3 rounded-xl border-2 text-center transition-all",
                          aiSettings.fidicThreshold === item.val
                            ? "border-orange-500 bg-orange-50/50 dark:bg-orange-950/20"
                            : "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-navy-950"
                        )}
                      >
                        <div className="text-xs font-bold text-navy-900 dark:text-white">
                          {item.label}
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5">{item.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* 3. Market Region for Cost Engine */}
                <div className="space-y-2">
                  <label className="block text-xs font-bold text-navy-900 dark:text-white">
                    {t("Primary Commodity Market Benchmark", "بنیادی ریٹ مارکیٹ (سیمنٹ و سریا)")}
                  </label>
                  <select
                    value={aiSettings.marketRegion}
                    onChange={(e) =>
                      setAiSettings({ ...aiSettings, marketRegion: e.target.value })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-1 focus:ring-orange-500 text-navy-900 dark:text-white font-medium"
                  >
                    <option value="lahore">Lahore (Badami Bagh & Multan Road steel mills)</option>
                    <option value="karachi">Karachi (Shershah & Port Qasim cement terminals)</option>
                    <option value="islamabad">Islamabad / Rawalpindi (I-9 Industrial Area)</option>
                  </select>
                </div>

                {/* 4. Automated Statutory Citations Toggle */}
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 flex items-center justify-between gap-4">
                  <div>
                    <h4 className="text-xs font-bold text-navy-900 dark:text-white">
                      {t("Mandatory Statutory Citations in AI Chat", "چیٹ میں بلڈنگ کوڈ دفعات کا حوالہ لازمی رکھیں")}
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Always ground responses with exact Chapter, Clause & Table numbers (e.g. PBC Section 4.2.1, Table 4.1).
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      setAiSettings((prev) => ({
                        ...prev,
                        autoCitations: !prev.autoCitations,
                      }))
                    }
                    className={cn(
                      "relative w-11 h-6 rounded-full transition-colors flex-shrink-0 cursor-pointer",
                      aiSettings.autoCitations ? "bg-orange-500" : "bg-slate-300 dark:bg-slate-700"
                    )}
                  >
                    <span
                      className={cn(
                        "absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow-xs",
                        aiSettings.autoCitations ? "left-5.5" : "left-0.5"
                      )}
                    />
                  </button>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="button"
                    onClick={handleSaveAIPreferences}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-orange-500 hover:bg-orange-600 shadow-sm shadow-orange-500/20 active:scale-95 transition-all"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>{t("Save AI Preferences", "اے آئی ترجیحات محفوظ کریں")}</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
