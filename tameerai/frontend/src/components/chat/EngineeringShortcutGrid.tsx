"use client";

import React from "react";
import {
  Calculator,
  ShieldCheck,
  BookOpen,
  ChartLine,
  FileSearch,
  CalendarDays,
  LucideIcon,
} from "lucide-react";
import { EngineeringShortcutCard } from "./EngineeringShortcutCard";

export interface ShortcutDefinition {
  id: string;
  title: string;
  titleUrdu: string;
  description: string;
  descriptionUrdu: string;
  href: string;
  icon: LucideIcon;
}

export const ENGINEERING_SHORTCUTS: ShortcutDefinition[] = [
  {
    id: "boq-costs",
    title: "BOQ & Cost Estimation",
    titleUrdu: "بی او کیو اور لاگت کا تخمینہ",
    description: "Explore available construction cost intelligence tools.",
    descriptionUrdu: "تعمیراتی لاگت اور تخمینہ کاری کے دستیاب ٹولز ملاحظہ کریں۔",
    href: "/dashboard/costs",
    icon: Calculator,
  },
  {
    id: "structural-safety",
    title: "Structural Safety",
    titleUrdu: "سٹرکچرل سیفٹی",
    description: "Access structural safety assessment and available hazard indicators.",
    descriptionUrdu: "سٹرکچرل سیفٹی کی جانچ اور خطرات کے انڈیکیٹرز دیکھیں۔",
    href: "/dashboard/safety",
    icon: ShieldCheck,
  },
  {
    id: "building-regulations",
    title: "Building Regulations",
    titleUrdu: "بلڈنگ ریگولیشنز",
    description: "Explore available building regulations and compliance information.",
    descriptionUrdu: "تعمیراتی قوانین اور قانونی تقاضوں کی معلومات دیکھیں۔",
    href: "/dashboard/regulations",
    icon: BookOpen,
  },
  {
    id: "material-rates",
    title: "Material Market Rates",
    titleUrdu: "مارکیٹ ریٹس برائے میٹریل",
    description: "Explore available material prices, grades and source information.",
    descriptionUrdu: "تعمیراتی سامان کے دستیاب ریٹس اور ذرائع ملاحظہ کریں۔",
    href: "/dashboard/costs",
    icon: ChartLine,
  },
  {
    id: "contract-analysis",
    title: "Contract Analysis",
    titleUrdu: "معاہدات کا تجزیہ",
    description: "Open the existing construction contract workspace.",
    descriptionUrdu: "تعمیراتی معاہدات اور فڈک شرائط کے لیے ورک سپیس کھولیں۔",
    href: "/dashboard/contracts",
    icon: FileSearch,
  },
  {
    id: "project-planning",
    title: "Project Planning",
    titleUrdu: "پروجیکٹ پلاننگ",
    description: "Explore your existing projects and available project information.",
    descriptionUrdu: "اپنے تعمیراتی منصوبوں اور ورک سپیس کا معائنہ کریں۔",
    href: "/dashboard/projects",
    icon: CalendarDays,
  },
];

interface EngineeringShortcutGridProps {
  language: "en" | "ur";
}

export function EngineeringShortcutGrid({ language }: EngineeringShortcutGridProps) {
  return (
    <div
      data-testid="engineering-shortcut-grid"
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-3.5 w-full max-w-4xl mx-auto pt-1"
    >
      {ENGINEERING_SHORTCUTS.map((shortcut) => (
        <EngineeringShortcutCard
          key={shortcut.id}
          id={shortcut.id}
          title={shortcut.title}
          titleUrdu={shortcut.titleUrdu}
          description={shortcut.description}
          descriptionUrdu={shortcut.descriptionUrdu}
          href={shortcut.href}
          icon={shortcut.icon}
          language={language}
        />
      ))}
    </div>
  );
}

