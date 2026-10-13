"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useLanguage } from "@/contexts/LanguageContext";
import { useTheme } from "next-themes";
import {
  Eye,
  EyeOff,
  Sun,
  Moon,
  Globe,
  ArrowRight,
  Mail,
  Lock,
  User,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import TameerLogo from "@/components/brand/TameerLogo";

interface AuthSplitScreenProps {
  initialMode?: "login" | "register";
}

const roles = [
  { en: "Civil Engineer", ur: "سول انجینئر", value: "engineer" },
  { en: "Contractor / Thekedar", ur: "ٹھیکیدار", value: "contractor" },
  { en: "Architect", ur: "آرکیٹیکٹ", value: "architect" },
  { en: "Construction Firm", ur: "تعمیراتی کمپنی", value: "company" },
];

export default function AuthSplitScreen({ initialMode = "login" }: AuthSplitScreenProps) {
  const { t, language, setLanguage } = useLanguage();
  const { theme, setTheme } = useTheme();

  const [mode, setMode] = useState<"login" | "register">(initialMode);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  // Form states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [selectedRole, setSelectedRole] = useState("engineer");
  const [rememberMe, setRememberMe] = useState(true);
  const [agreeTerms, setAgreeTerms] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      window.location.href = "/dashboard";
    }, 1000);
  };

  const handleGoogleAuth = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      window.location.href = "/dashboard";
    }, 800);
  };

  return (
    <div className="min-h-screen w-full flex bg-slate-50 dark:bg-navy-950 text-slate-900 dark:text-slate-100">
      {/* ========================================================= */}
      {/* LEFT SIDE: Exactly 50% Width - Construction AI Showcase   */}
      {/* ========================================================= */}
      <div className="hidden lg:flex lg:w-1/2 sticky top-0 h-screen relative flex-col justify-between p-8 xl:p-10 overflow-hidden bg-navy-950 flex-shrink-0">
        {/* Background Image */}
        <Image
          src="/auth-hero.jpg"
          alt="Pakistani Civil Engineer on Construction Site with Holographic AI BIM Blueprint"
          fill
          priority
          sizes="(min-width: 1024px) 50vw, 100vw"
          className="object-cover object-center"
        />

        {/* Ambient Dark Gradient Overlays */}
        <div className="absolute inset-0 bg-gradient-to-t from-navy-950 via-navy-950/45 to-navy-950/70" />
        <div className="absolute inset-0 bg-gradient-to-r from-navy-950/70 via-transparent to-navy-950/20" />

        {/* Top Header on Left Side */}
        <div className="relative z-10 flex items-center justify-between">
          <Link href="/" className="inline-block transition-transform hover:scale-105">
            <TameerLogo variant="full" size="sm" theme="dark" showTagline={true} />
          </Link>
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-md border border-white/15 text-xs font-semibold text-white/90">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>{t("PBC 2021 Ready", "پی بی سی 2021 مصدقہ")}</span>
          </div>
        </div>

        {/* Floating Holographic AI Badges in Center Area */}
        <div className="relative z-10 my-auto py-6 max-w-md space-y-4">
          {/* Badge 1 */}
          <div className="p-4 rounded-2xl bg-navy-900/80 backdrop-blur-xl border border-white/15 shadow-2xl flex items-center gap-3.5 transition-transform hover:translate-x-1">
            <div className="w-11 h-11 rounded-xl bg-orange-500/20 border border-orange-500/30 flex items-center justify-center flex-shrink-0 text-orange-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <p className="text-[10px] font-bold text-orange-400 uppercase tracking-wider">
                {t("AI Structural Verification", "اے آئی سٹرکچرل تصدیق")}
              </p>
              <h4 className="text-sm font-semibold text-white mt-0.5">
                {t("34 Code Compliance Checks / Second", "34 بلڈنگ کوڈ شقیں فی سیکنڈ تصدیق")}
              </h4>
            </div>
          </div>

          {/* Badge 2 */}
          <div className="p-4 rounded-2xl bg-navy-900/80 backdrop-blur-xl border border-white/15 shadow-2xl flex items-center gap-3.5 transition-transform hover:translate-x-1">
            <div className="w-11 h-11 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center flex-shrink-0 text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <p className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
                {t("Real-Time Cost Intelligence", "ریئل ٹائم تعمیراتی لاگت انٹیلی جنس")}
              </p>
              <h4 className="text-sm font-semibold text-white mt-0.5">
                {t("Lahore, Karachi & Islamabad Live Steel & Cement Rates", "لاہور، کراچی اور اسلام آباد لائیو میٹریل ریٹس")}
              </h4>
            </div>
          </div>
        </div>

        {/* Bottom Social Proof on Left Side */}
        <div className="relative z-10 pt-4 border-t border-white/15">
          <p className="text-xs text-slate-200 font-medium leading-relaxed max-w-md">
            &ldquo;
            {t(
              "TameerAI brings structural precision, building code compliance, and real-time cost intelligence to civil engineering teams across Pakistan.",
              "TameerAI پاکستان بھر کی انجینئرنگ اور کنسٹرکشن ٹیموں کو خودکار ضوابط، سٹرکچرل درستگی اور لاگت انٹیلی جنس فراہم کرتا ہے۔"
            )}
            &rdquo;
          </p>
          <div className="mt-3 flex items-center gap-2.5">
            <div className="flex -space-x-1.5">
              <div className="w-6 h-6 rounded-full bg-orange-500 border-2 border-navy-950 flex items-center justify-center text-[9px] font-black text-white">
                PK
              </div>
              <div className="w-6 h-6 rounded-full bg-emerald-600 border-2 border-navy-950 flex items-center justify-center text-[9px] font-black text-white">
                CE
              </div>
              <div className="w-6 h-6 rounded-full bg-blue-600 border-2 border-navy-950 flex items-center justify-center text-[9px] font-black text-white">
                AR
              </div>
            </div>
            <span className="text-xs text-slate-300 font-medium">
              {t("Trusted by 1,200+ engineers & contractors", "1,200+ انجینئرز اور ٹھیکیداروں کا اعتماد")}
            </span>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* RIGHT SIDE: Exactly 50% Width - Form with Natural Scroll  */}
      {/* ========================================================= */}
      <div className="w-full lg:w-1/2 min-h-screen flex flex-col justify-between p-6 sm:p-8 lg:p-8 xl:p-12 overflow-y-auto">
        {/* Top Control Bar: Logo, Language, Theme Toggle */}
        <div className="flex items-center justify-between mb-4 flex-shrink-0">
          <div className="lg:hidden">
            <Link href="/">
              <TameerLogo variant="full" size="xs" />
            </Link>
          </div>

          <div className="hidden lg:block">
            <Link
              href="/"
              className="text-xs font-semibold text-slate-500 hover:text-orange-500 dark:text-slate-400 dark:hover:text-orange-400 flex items-center gap-1 transition-colors"
            >
              ← {t("Back to Home", "مرکزی صفحہ")}
            </Link>
          </div>

          {/* Controls: Language Switch + Dark Mode */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setLanguage(language === "en" ? "ur" : "en")}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:border-orange-500/50 transition-all shadow-2xs"
            >
              <Globe className="w-3.5 h-3.5 text-orange-500" />
              <span>{language === "en" ? "اردو" : "English"}</span>
            </button>

            <button
              type="button"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="p-2 rounded-xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:text-orange-500 dark:hover:text-orange-400 transition-all shadow-2xs"
              aria-label="Toggle dark mode"
            >
              {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Center Card Container */}
        <div className="w-full max-w-md mx-auto my-auto py-4">
          {/* Segmented Tab Controls: Login vs Register */}
          <div className="grid grid-cols-2 p-1.5 bg-slate-100 dark:bg-navy-900 rounded-2xl mb-6 border border-slate-200/80 dark:border-slate-800">
            <button
              type="button"
              onClick={() => setMode("login")}
              className={`py-2 text-xs sm:text-sm font-bold rounded-xl transition-all ${
                mode === "login"
                  ? "bg-white dark:bg-navy-800 text-navy-900 dark:text-white shadow-2xs"
                  : "text-slate-500 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white"
              }`}
            >
              {t("Login", "سائن ان (Login)")}
            </button>
            <button
              type="button"
              onClick={() => setMode("register")}
              className={`py-2 text-xs sm:text-sm font-bold rounded-xl transition-all ${
                mode === "register"
                  ? "bg-white dark:bg-navy-800 text-navy-900 dark:text-white shadow-2xs"
                  : "text-slate-500 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white"
              }`}
            >
              {t("Register", "رجسٹر (Register)")}
            </button>
          </div>

          {/* Form Header */}
          <div className="mb-6 text-center sm:text-left">
            <h1 className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white tracking-tight">
              {mode === "login"
                ? t("Welcome back", "خوش آمدید")
                : t("Create your account", "نیا اکاؤنٹ بنائیں")}
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
              {mode === "login"
                ? t(
                    "Sign in to access your projects and compliance intelligence.",
                    "اپنے پروجیکٹس اور تعمیل انٹیلی جنس تک رسائی کے لیے لاگ ان کریں۔"
                  )
                : t(
                    "Start your 14-day free trial. Instant access to PBC 2021 audits.",
                    "14 دن کا مفت ٹرائل شروع کریں۔ پی بی سی 2021 آڈٹ تک فوری رسائی۔"
                  )}
            </p>
          </div>

          {/* Main Credentials Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* If Register: Full Name */}
            {mode === "register" && (
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                  {t("Full Name", "پورا نام")}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <User className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder={language === "ur" ? "انجینئر علی خان" : "Engr. Ali Khan"}
                    className="w-full pl-10 pr-3.5 py-2.5 sm:py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-900 text-xs sm:text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all placeholder:text-slate-400 shadow-2xs"
                  />
                </div>
              </div>
            )}

            {/* If Register: Professional Role as Clickable Cards */}
            {mode === "register" && (
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                  {t("Professional Role", "پیشہ ورانہ شعبہ")}
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {roles.map((r) => (
                    <button
                      key={r.value}
                      type="button"
                      onClick={() => setSelectedRole(r.value)}
                      className={`px-3.5 py-2.5 rounded-xl text-xs font-semibold border text-left transition-all ${
                        selectedRole === r.value
                          ? "bg-orange-500/10 border-orange-500 text-orange-600 dark:text-orange-400 font-bold shadow-xs ring-1 ring-orange-500/20"
                          : "border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-navy-900"
                      }`}
                    >
                      {t(r.en, r.ur)}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Email Field */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                {t("Email Address", "ای میل پتہ")}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="engr.ali@construction.pk"
                  className="w-full pl-10 pr-3.5 py-2.5 sm:py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-900 text-xs sm:text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all placeholder:text-slate-400 shadow-2xs"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  {t("Password", "پاس ورڈ")}
                </label>
                {mode === "login" && (
                  <a
                    href="#"
                    className="text-xs font-semibold text-orange-600 dark:text-orange-400 hover:underline"
                  >
                    {t("Forgot?", "بھول گئے؟")}
                  </a>
                )}
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-10 py-2.5 sm:py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-900 text-xs sm:text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all placeholder:text-slate-400 shadow-2xs"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Checkbox Rows */}
            {mode === "login" ? (
              <div className="flex items-center pt-1">
                <input
                  id="remember-me"
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded text-orange-500 focus:ring-orange-400 border-slate-300 dark:border-slate-700 bg-white dark:bg-navy-900 cursor-pointer"
                />
                <label
                  htmlFor="remember-me"
                  className="ml-2.5 text-xs text-slate-600 dark:text-slate-400 cursor-pointer"
                >
                  {t("Remember this device", "اس ڈیوائس کو یاد رکھیں")}
                </label>
              </div>
            ) : (
              <div className="flex items-start pt-1">
                <input
                  id="agree-terms"
                  type="checkbox"
                  checked={agreeTerms}
                  onChange={(e) => setAgreeTerms(e.target.checked)}
                  className="w-4 h-4 mt-0.5 rounded text-orange-500 focus:ring-orange-400 border-slate-300 dark:border-slate-700 bg-white dark:bg-navy-900 cursor-pointer"
                />
                <label
                  htmlFor="agree-terms"
                  className="ml-2.5 text-xs text-slate-600 dark:text-slate-400 cursor-pointer leading-tight"
                >
                  {t(
                    "I agree to TameerAI's Terms & Privacy Policy.",
                    "میں TameerAI کی شرائط سے اتفاق کرتا ہوں۔"
                  )}
                </label>
              </div>
            )}

            {/* Main Action Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-3 py-3 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 shadow-md shadow-orange-500/20 active:scale-[0.99] transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : mode === "login" ? (
                <>
                  <span>{t("Login to Workspace", "ورک اسپیس میں لاگ ان کریں")}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              ) : (
                <>
                  <span>{t("Create Account", "اکاؤنٹ بنائیں")}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative flex items-center justify-center my-5">
            <div className="border-t border-slate-200 dark:border-slate-800 w-full" />
            <span className="bg-slate-50 dark:bg-navy-950 px-3 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider whitespace-nowrap">
              {t("or continue with", "یا جاری رکھیں")}
            </span>
          </div>

          {/* Google Login Option - NOW AT THE BOTTOM */}
          <button
            type="button"
            onClick={handleGoogleAuth}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 py-2.5 px-4 bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-navy-800/80 rounded-xl font-semibold text-xs sm:text-sm text-slate-700 dark:text-slate-200 transition-all shadow-2xs hover:border-slate-300 dark:hover:border-slate-700 group"
          >
            <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            <span>
              {mode === "login"
                ? t("Continue with Google", "گوگل کے ساتھ جاری رکھیں")
                : t("Sign up with Google", "گوگل کے ساتھ سائن اپ کریں")}
            </span>
          </button>

          {/* Toggle Switcher at Bottom */}
          <div className="mt-5 text-center text-xs text-slate-500 dark:text-slate-400">
            {mode === "login" ? (
              <p>
                {t("Don't have an account?", "اکاؤنٹ نہیں ہے؟")}{" "}
                <button
                  type="button"
                  onClick={() => setMode("register")}
                  className="font-bold text-orange-600 dark:text-orange-400 hover:underline ml-1"
                >
                  {t("Create Account", "اکاؤنٹ بنائیں")}
                </button>
              </p>
            ) : (
              <p>
                {t("Already have an account?", "پہلے سے اکاؤنٹ ہے؟")}{" "}
                <button
                  type="button"
                  onClick={() => setMode("login")}
                  className="font-bold text-orange-600 dark:text-orange-400 hover:underline ml-1"
                >
                  {t("Log In", "لاگ ان")}
                </button>
              </p>
            )}
          </div>
        </div>

        {/* Footer Guarantee */}
        <div className="pt-4 border-t border-slate-200/80 dark:border-slate-800 flex items-center justify-between text-xs text-slate-400 dark:text-slate-500 flex-shrink-0">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
            <span>{t("256-bit SSL Encryption", "256-بٹ ایس ایس ایل انکرپشن")}</span>
          </div>
          <div className="flex items-center gap-3">
            <a href="#" className="hover:underline">
              {t("Privacy", "رازداری")}
            </a>
            <span>•</span>
            <a href="#" className="hover:underline">
              {t("Terms", "شرائط")}
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
