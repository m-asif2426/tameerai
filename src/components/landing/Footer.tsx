"use client";

import { useLanguage } from "@/contexts/LanguageContext";
import Link from "next/link";
import { Mail, Phone, MapPin, ArrowRight, Globe, Share2, MessageSquare } from "lucide-react";
import TameerLogo from "@/components/brand/TameerLogo";

const footerLinks = {
  product: {
    en: "Product",
    ur: "پروڈکٹ",
    links: [
      { en: "Compliance AI", ur: "تعمیل اے آئی", href: "#" },
      { en: "Contract Analyzer", ur: "معاہدہ تجزیہ کار", href: "#" },
      { en: "Cost Intelligence", ur: "لاگت انٹیلی جنس", href: "#" },
      { en: "Urdu Assistant", ur: "اردو اسسٹنٹ", href: "#" },
      { en: "Reports", ur: "رپورٹس", href: "#" },
    ],
  },
  company: {
    en: "Company",
    ur: "کمپنی",
    links: [
      { en: "About Us", ur: "ہمارے بارے میں", href: "#about" },
      { en: "Blog", ur: "بلاگ", href: "#" },
      { en: "Careers", ur: "کیریئر", href: "#" },
      { en: "Press", ur: "پریس", href: "#" },
    ],
  },
  legal: {
    en: "Legal",
    ur: "قانونی",
    links: [
      { en: "Privacy Policy", ur: "رازداری کی پالیسی", href: "#" },
      { en: "Terms of Service", ur: "خدمت کی شرائط", href: "#" },
      { en: "Cookie Policy", ur: "کوکی پالیسی", href: "#" },
    ],
  },
};

export default function Footer() {
  const { t } = useLanguage();

  return (
    <footer id="about" className="bg-navy-900 dark:bg-black text-white">
      {/* CTA Banner */}
      <div className="border-b border-slate-800">
        <div className="container-custom py-16">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h2 className="text-3xl font-bold mb-3">
                {t("Ready to Build Smarter?", "سمارٹ تعمیر کے لیے تیار ہیں؟")}
              </h2>
              <p className="text-slate-400">
                {t(
                  "Join 500+ construction professionals already using TameerAI across Pakistan.",
                  "پاکستان بھر میں TameerAI استعمال کرنے والے 500+ تعمیراتی پیشہ ور افراد میں شامل ہوں۔"
                )}
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                href="/signup"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-xl transition-all"
              >
                {t("Start Free Trial", "مفت ٹرائل شروع کریں")}
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="#"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 font-semibold rounded-xl transition-all"
              >
                {t("Book Demo", "ڈیمو بک کریں")}
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Main Footer */}
      <div className="container-custom py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8">
          {/* Brand */}
          <div className="col-span-2">
            <div className="mb-4">
              <TameerLogo variant="full" size="md" theme="dark" showTagline={true} />
            </div>
            <p className="text-sm text-slate-400 mb-5 max-w-xs leading-relaxed">
              {t(
                "Pakistan's first AI-powered construction compliance and cost intelligence platform.",
                "پاکستان کا پہلا اے آئی سے چلنے والا تعمیراتی تعمیل اور لاگت انٹیلی جنس پلیٹ فارم۔"
              )}
            </p>
            <div className="space-y-2 text-sm text-slate-400">
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-orange-500" />
                <span>hello@tameerai.pk</span>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-orange-500" />
                <span>+92 42 1234 5678</span>
              </div>
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-orange-500" />
                <span>{t("Lahore, Pakistan", "لاہور، پاکستان")}</span>
              </div>
            </div>
            <div className="flex items-center gap-3 mt-5">
              {[Globe, Share2, MessageSquare].map((Icon, i) => (
                <button
                  key={i}
                  className="w-8 h-8 bg-slate-800 hover:bg-slate-700 rounded-lg flex items-center justify-center transition-colors text-slate-400 hover:text-white"
                  aria-label="Social Link"
                >
                  <Icon className="w-4 h-4" />
                </button>
              ))}
            </div>
          </div>

          {/* Links */}
          {Object.values(footerLinks).map((section, i) => (
            <div key={i}>
              <h4 className="text-sm font-semibold text-white mb-4">
                {t(section.en, section.ur)}
              </h4>
              <ul className="space-y-2.5">
                {section.links.map((link, j) => (
                  <li key={j}>
                    <a
                      href={link.href}
                      className="text-sm text-slate-400 hover:text-white transition-colors"
                    >
                      {t(link.en, link.ur)}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-slate-500">
            © 2024 TameerAI. {t("All rights reserved.", "تمام حقوق محفوظ ہیں۔")}
          </p>
          <p className="text-xs text-slate-500">
            {t("Made with ❤️ in Pakistan", "پاکستان میں ❤️ سے بنایا گیا")}
          </p>
        </div>
      </div>
    </footer>
  );
}
