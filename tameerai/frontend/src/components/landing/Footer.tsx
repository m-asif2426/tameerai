"use client";

import { useLanguage } from "@/contexts/LanguageContext";
import Link from "next/link";
import { Mail, Phone, MapPin, ArrowRight } from "lucide-react";
import TameerLogo from "@/components/brand/TameerLogo";

// Standard brand SVG icons for the 4 verified platforms
function FacebookIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
    </svg>
  );
}

function InstagramIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
    </svg>
  );
}

function LinkedInIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.762-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
    </svg>
  );
}

function YouTubeIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
    </svg>
  );
}

const footerLinks = {
  platform: {
    en: "Platform",
    ur: "پلیٹ فارم",
    links: [
      { en: "Material Rate Intelligence", ur: "تعمیراتی ریٹ انٹیلی جنس", href: "#rates" },
      { en: "Structural Safety Advisory", ur: "سٹرکچرل سیفٹی ایڈوائزری", href: "#safety" },
      { en: "Statutory Regulations", ur: "عمارتی ضوابط و قوانین", href: "#regulations" },
      { en: "FIDIC Contract Risk Analyzer", ur: "فڈک معاہدہ تجزیہ کار", href: "#contracts" },
      { en: "BOQ & Cost Breakdown", ur: "بی او کیو لاگت تجزیہ", href: "#costs" },
    ],
  },
  company: {
    en: "Company",
    ur: "کمپنی",
    links: [
      { en: "About TameerAI", ur: "ہمارے بارے میں", href: "#about" },
      { en: "Engineering Oversight", ur: "انجینئرنگ نگرانی", href: "#about" },
      { en: "PEC Compliance", ur: "پی ای سی ضوابط", href: "#safety" },
      { en: "Careers", ur: "کیریئر", href: "#" },
    ],
  },
  legal: {
    en: "Legal & Regulatory",
    ur: "قانونی اور ضوابط",
    links: [
      { en: "Privacy Policy", ur: "رازداری کی پالیسی", href: "#" },
      { en: "Terms of Service", ur: "خدمت کی شرائط", href: "#" },
      { en: "Statutory Notice", ur: "قانونی نوٹس", href: "#" },
    ],
  },
};

const socialChannels = [
  { name: "Facebook", icon: FacebookIcon, href: "#" },
  { name: "Instagram", icon: InstagramIcon, href: "#" },
  { name: "LinkedIn", icon: LinkedInIcon, href: "#" },
  { name: "YouTube", icon: YouTubeIcon, href: "#" },
];

export default function Footer() {
  const { t } = useLanguage();

  return (
    <footer id="about" className="relative bg-navy-900 dark:bg-black text-white">
      <div id="contact" className="absolute -top-16" />
      {/* Call To Action Banner */}
      <div className="border-b border-slate-800">
        <div className="container-custom py-14">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h2 className="text-2xl sm:text-3xl font-bold mb-3">
                {t("Ready to Build Smarter & Safer?", "سمارٹ اور محفوظ تعمیر کے لیے تیار ہیں؟")}
              </h2>
              <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
                {t(
                  "Empower your construction projects with real-time market rates, statutory compliance, and structural safety intelligence.",
                  "اپنے تعمیراتی منصوبوں کو لائیو مارکیٹ ریٹس، قانونی ضوابط اور سٹرکچرل سیفٹی انٹیلی جنس سے بااختیار بنائیں۔"
                )}
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 md:justify-end">
              <Link
                href="/signup"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-xl transition-all shadow-md shadow-orange-500/20"
              >
                {t("Start Free Workspace", "مفت ورک اسپیس بنائیں")}
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/login"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 font-semibold rounded-xl transition-all"
              >
                {t("Sign In", "لاگ ان کریں")}
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Main Footer Directory */}
      <div className="container-custom py-12">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-8">
          {/* Brand Info */}
          <div className="md:col-span-2 space-y-4">
            <TameerLogo variant="full" size="md" theme="dark" showTagline={true} />
            <p className="text-sm text-slate-400 max-w-sm leading-relaxed">
              {t(
                "Pakistan's premier construction intelligence platform: unifying real-time material price intelligence, statutory building regulations, and structural safety advisory.",
                "پاکستان کا ممتاز تعمیراتی انٹیلی جنس پلیٹ فارم: مارکیٹ ریٹس، بلڈنگ بائی لاز اور سٹرکچرل سیفٹی کا مستند نظام۔"
              )}
            </p>

            <div className="space-y-2.5 text-sm text-slate-300 pt-2">
              <div className="flex items-center gap-2.5">
                <Mail className="w-4 h-4 text-orange-500 flex-shrink-0" />
                <a href="mailto:tameerai@gmail.com" className="hover:text-white transition-colors">
                  tameerai@gmail.com
                </a>
              </div>
              <div className="flex items-center gap-2.5">
                <Phone className="w-4 h-4 text-orange-500 flex-shrink-0" />
                <a href="tel:03145025152" className="hover:text-white transition-colors">
                  03145025152
                </a>
              </div>
              <div className="flex items-center gap-2.5">
                <MapPin className="w-4 h-4 text-orange-500 flex-shrink-0" />
                <span>{t("Lahore / Islamabad / Karachi, Pakistan", "لاہور / اسلام آباد / کراچی، پاکستان")}</span>
              </div>
            </div>

            {/* Social Media Channels (Verified placeholders: inactive until official URLs provided) */}
            <div className="flex items-center gap-2.5 pt-3">
              {socialChannels.map((channel) => {
                const IconComponent = channel.icon;
                return (
                  <span
                    key={channel.name}
                    role="button"
                    tabIndex={-1}
                    aria-disabled="true"
                    title={`${channel.name} — ${t("Official social profile coming soon", "سرکاری پروفائل جلد فراہم کی جائے گی")}`}
                    className="w-9 h-9 bg-slate-800/80 border border-slate-700/60 text-slate-500 rounded-lg flex items-center justify-center cursor-not-allowed transition-colors"
                  >
                    <IconComponent className="w-4 h-4" />
                  </span>
                );
              })}
            </div>
          </div>

          {/* Links Columns */}
          {Object.values(footerLinks).map((section, i) => (
            <div key={i} className="space-y-3">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
                {t(section.en, section.ur)}
              </h3>
              <ul className="space-y-2">
                {section.links.map((link, j) => (
                  <li key={j}>
                    <a
                      href={link.href}
                      className="text-sm text-slate-400 hover:text-orange-400 transition-colors"
                    >
                      {t(link.en, link.ur)}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Attribution Bar */}
        <div className="mt-12 pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© 2026 TameerAI. {t("All rights reserved.", "تمام حقوق محفوظ ہیں۔")}</p>
          <p>
            {t(
              "Built for Pakistan's Construction Industry",
              "پاکستان کی تعمیراتی صنعت کے لیے تیار کردہ"
            )}
          </p>
        </div>
      </div>
    </footer>
  );
}
