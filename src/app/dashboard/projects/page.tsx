"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  Building2,
  MapPin,
  Calendar,
  Users,
  TrendingUp,
  ShieldCheck,
  Search,
  Filter,
  ArrowUpDown,
  Plus,
  Eye,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  MoreVertical,
  X,
  UploadCloud,
  ChevronRight,
  Layers,
  ArrowRight,
  Sparkles,
  LayoutGrid,
  List,
} from "lucide-react";
import { cn } from "@/lib/utils";

import { Project, ProjectCity, ProjectStatus, ProjectRisk } from "@/types";
import { INITIAL_PROJECTS } from "@/data";

export default function ProjectsPage() {
  const { t } = useLanguage();

  const [projects, setProjects] = useState<Project[]>(INITIAL_PROJECTS);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [riskFilter, setRiskFilter] = useState<string>("all");
  const [cityFilter, setCityFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"recent" | "budgetDesc" | "budgetAsc" | "risk" | "name">("recent");
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");

  // Create Project Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectLocation, setNewProjectLocation] = useState("");
  const [newProjectCity, setNewProjectCity] = useState<"Lahore" | "Karachi" | "Islamabad">("Lahore");
  const [newProjectBudgetCrore, setNewProjectBudgetCrore] = useState("10");
  const [newProjectType, setNewProjectType] = useState("Commercial G+8");

  // Filtering & Sorting logic
  const filteredProjects = useMemo(() => {
    return projects
      .filter((p) => {
        const matchesSearch =
          p.name.toLowerCase().includes(search.toLowerCase()) ||
          p.location.toLowerCase().includes(search.toLowerCase()) ||
          p.engineer.toLowerCase().includes(search.toLowerCase()) ||
          p.id.toLowerCase().includes(search.toLowerCase());

        const matchesStatus =
          statusFilter === "all" || p.status.toLowerCase() === statusFilter.toLowerCase();

        const matchesRisk =
          riskFilter === "all" || p.risk.toLowerCase() === riskFilter.toLowerCase();

        const matchesCity =
          cityFilter === "all" || p.city.toLowerCase() === cityFilter.toLowerCase();

        return matchesSearch && matchesStatus && matchesRisk && matchesCity;
      })
      .sort((a, b) => {
        if (sortBy === "budgetDesc") return b.budgetCrore - a.budgetCrore;
        if (sortBy === "budgetAsc") return a.budgetCrore - b.budgetCrore;
        if (sortBy === "name") return a.name.localeCompare(b.name);
        if (sortBy === "risk") {
          const riskWeight = { High: 3, Medium: 2, Low: 1 };
          return riskWeight[b.risk] - riskWeight[a.risk];
        }
        return 0; // Default recent
      });
  }, [projects, search, statusFilter, riskFilter, cityFilter, sortBy]);

  // Handle New Project submission
  const handleCreateProject = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName) return;

    const newProject: Project = {
      id: `PRJ-00${projects.length + 1}`,
      name: newProjectName,
      nameUrdu: newProjectName,
      location: `${newProjectLocation || "Main Boulevard"}, ${newProjectCity}`,
      city: newProjectCity,
      cityUrdu: newProjectCity === "Lahore" ? "لاہور" : newProjectCity === "Karachi" ? "کراچی" : "اسلام آباد",
      type: newProjectType,
      typeUrdu: newProjectType,
      budgetCrore: parseFloat(newProjectBudgetCrore) || 10,
      budgetRaw: (parseFloat(newProjectBudgetCrore) || 10) * 10000000,
      spentCrore: 0,
      status: "Under Analysis",
      statusUrdu: "زیرِ تجزیہ (Under Analysis)",
      risk: "Low",
      riskUrdu: "کم (Low)",
      complianceScore: 100,
      lastUpdate: "Just now",
      lastUpdateUrdu: "ابھی",
      floors: 6,
      areaSqft: "25,000 sq ft",
      engineer: "Aslam Bhai",
    };

    setProjects([newProject, ...projects]);
    setIsModalOpen(false);
    setNewProjectName("");
    setNewProjectLocation("");
  };

  const getStatusBadge = (status: Project["status"]) => {
    switch (status) {
      case "Active":
        return "bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800";
      case "Under Analysis":
        return "bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800";
      case "Planning":
        return "bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-800";
      case "Completed":
        return "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700";
    }
  };

  const getRiskBadge = (risk: Project["risk"]) => {
    switch (risk) {
      case "Low":
        return {
          badge: "bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800",
          dot: "bg-emerald-500",
        };
      case "Medium":
        return {
          badge: "bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-800",
          dot: "bg-amber-500",
        };
      case "High":
        return {
          badge: "bg-red-50 dark:bg-red-950/50 text-red-600 dark:text-red-400 border-red-200 dark:border-red-800",
          dot: "bg-red-500 animate-pulse",
        };
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* ========================================================= */}
      {/* 1. HEADER: "My Projects" + "+ Create New Project"        */}
      {/* ========================================================= */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white tracking-tight">
              {t("My Projects", "میرے منصوبے (My Projects)")}
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-orange-100 dark:bg-orange-950 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-800">
              {projects.length} {t("Projects", "منصوبے")}
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t(
              "Manage site blueprints, PBC 2021 code compliance, and budget tracking across all active construction sites.",
              "تمام تعمیراتی سائٹس، بلڈنگ کوڈز کی تعمیل اور بجٹ کی نگرانی ایک جگہ پر کریں۔"
            )}
          </p>
        </div>

        {/* Primary Action: + Create New Project */}
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-orange-500/25 transition-all active:scale-95 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4 stroke-[3]" />
          <span>{t("Create New Project", "نیا پروجیکٹ بنائیں")}</span>
        </button>
      </div>

      {/* ========================================================= */}
      {/* 2. CONSTRUCTION KPI SUMMARY STRIP                         */}
      {/* ========================================================= */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {t("Total Portfolio Budget", "کل پورٹ فولیو بجٹ")}
          </p>
          <p className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white mt-1">
            PKR 105.0 {t("Crore", "کروڑ")}
          </p>
          <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">
            {t("6 Monitored Properties", "6 زیرِ نگرانی سائٹس")}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {t("Under Analysis", "زیرِ تجزیہ آڈٹس")}
          </p>
          <p className="text-xl sm:text-2xl font-black text-amber-600 dark:text-amber-400 mt-1">
            2 {t("Projects", "منصوبے")}
          </p>
          <span className="text-[10px] text-slate-500 dark:text-slate-400">
            {t("DHA Plaza & Factory Project", "ڈی ایچ اے اور فیکٹری")}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {t("Average Compliance", "اوسط تعمیل اسکور")}
          </p>
          <p className="text-xl sm:text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1">
            89.3%
          </p>
          <span className="text-[10px] text-slate-500 dark:text-slate-400">
            {t("PBC 2021 Certified", "پی بی سی 2021 تصدیق شدہ")}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {t("High Risk Alerts", "ہائی رسک الرٹس")}
          </p>
          <p className="text-xl sm:text-2xl font-black text-red-600 dark:text-red-400 mt-1">
            1 {t("Critical", "اہم")}
          </p>
          <span className="text-[10px] text-red-600 dark:text-red-400 font-semibold">
            {t("Fire Exit Corridor Notice", "فائر ایسکیپ نوٹس")}
          </span>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 3. TOOLBAR: Search, Filter & Sort                         */}
      {/* ========================================================= */}
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3 p-3 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t(
              "Search by project name, location, or engineer...",
              "منصوبے کا نام، مقام یا انجینئر تلاش کریں..."
            )}
            className="w-full pl-10 pr-4 py-2 text-xs rounded-xl bg-slate-100/70 dark:bg-navy-950 border border-transparent focus:border-orange-500/50 text-navy-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-500/20"
          />
        </div>

        {/* Filter & Sort Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Status Filter */}
          <div className="flex items-center gap-1.5 bg-slate-100/70 dark:bg-navy-950 px-2.5 py-1.5 rounded-xl border border-slate-200/60 dark:border-slate-800">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent text-xs font-semibold text-slate-700 dark:text-slate-300 focus:outline-none cursor-pointer"
            >
              <option value="all">{t("All Statuses", "تمام حالات")}</option>
              <option value="Under Analysis">{t("Under Analysis", "زیرِ تجزیہ")}</option>
              <option value="Active">{t("Active", "فعال")}</option>
              <option value="Planning">{t("Planning", "منصوبہ بندی")}</option>
              <option value="Completed">{t("Completed", "مکمل")}</option>
            </select>
          </div>

          {/* Risk Filter */}
          <div className="flex items-center gap-1.5 bg-slate-100/70 dark:bg-navy-950 px-2.5 py-1.5 rounded-xl border border-slate-200/60 dark:border-slate-800">
            <span className="text-[11px] font-bold text-slate-400">{t("Risk:", "خطرہ:")}</span>
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="bg-transparent text-xs font-semibold text-slate-700 dark:text-slate-300 focus:outline-none cursor-pointer"
            >
              <option value="all">{t("All Risks", "تمام درجات")}</option>
              <option value="Low">{t("Low Risk", "کم خطرہ")}</option>
              <option value="Medium">{t("Medium Risk", "درمیانہ")}</option>
              <option value="High">{t("High Risk", "زیادہ خطرہ")}</option>
            </select>
          </div>

          {/* City Filter */}
          <div className="flex items-center gap-1.5 bg-slate-100/70 dark:bg-navy-950 px-2.5 py-1.5 rounded-xl border border-slate-200/60 dark:border-slate-800">
            <MapPin className="w-3.5 h-3.5 text-orange-500" />
            <select
              value={cityFilter}
              onChange={(e) => setCityFilter(e.target.value)}
              className="bg-transparent text-xs font-semibold text-slate-700 dark:text-slate-300 focus:outline-none cursor-pointer"
            >
              <option value="all">{t("All Cities", "تمام شہر")}</option>
              <option value="Lahore">{t("Lahore", "لاہور")}</option>
              <option value="Karachi">{t("Karachi", "کراچی")}</option>
              <option value="Islamabad">{t("Islamabad", "اسلام آباد")}</option>
            </select>
          </div>

          {/* Sort Selector */}
          <div className="flex items-center gap-1.5 bg-slate-100/70 dark:bg-navy-950 px-2.5 py-1.5 rounded-xl border border-slate-200/60 dark:border-slate-800">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-transparent text-xs font-semibold text-slate-700 dark:text-slate-300 focus:outline-none cursor-pointer"
            >
              <option value="recent">{t("Recently Updated", "حالیہ اپ ڈیٹ")}</option>
              <option value="budgetDesc">{t("Budget: High to Low", "بجٹ: زیادہ سے کم")}</option>
              <option value="budgetAsc">{t("Budget: Low to High", "بجٹ: کم سے زیادہ")}</option>
              <option value="risk">{t("Risk Priority", "خطرے کی بنیاد پر")}</option>
              <option value="name">{t("Name: A to Z", "نام الف ب")}</option>
            </select>
          </div>

          {/* View Mode Toggle: Grid vs Table */}
          <div className="flex items-center bg-slate-100/70 dark:bg-navy-950 p-1 rounded-xl border border-slate-200/60 dark:border-slate-800">
            <button
              onClick={() => setViewMode("grid")}
              className={cn(
                "p-1.5 rounded-lg text-xs transition-colors",
                viewMode === "grid"
                  ? "bg-white dark:bg-navy-800 text-orange-500 shadow-2xs font-bold"
                  : "text-slate-400 hover:text-navy-900 dark:hover:text-white"
              )}
              title="Grid View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode("table")}
              className={cn(
                "p-1.5 rounded-lg text-xs transition-colors",
                viewMode === "table"
                  ? "bg-white dark:bg-navy-800 text-orange-500 shadow-2xs font-bold"
                  : "text-slate-400 hover:text-navy-900 dark:hover:text-white"
              )}
              title="Table View"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 4. PROJECTS LIST: Card View (Default) or Table View       */}
      {/* ========================================================= */}
      {filteredProjects.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800">
          <Building2 className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
          <h3 className="text-base font-bold text-navy-900 dark:text-white">
            {t("No projects found", "کوئی پروجیکٹ نہیں ملا")}
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {t("Try clearing search filters or create a new construction project.", "فلٹرز تبدیل کریں یا نیا پروجیکٹ شامل کریں۔")}
          </p>
          <button
            onClick={() => {
              setSearch("");
              setStatusFilter("all");
              setRiskFilter("all");
              setCityFilter("all");
            }}
            className="mt-4 px-4 py-2 rounded-xl text-xs font-bold bg-slate-100 dark:bg-navy-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200"
          >
            {t("Reset Filters", "فلٹرز ری سیٹ کریں")}
          </button>
        </div>
      ) : viewMode === "grid" ? (
        /* GRID VIEW OF PROJECT CARDS */
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => {
            const riskConfig = getRiskBadge(project.risk);
            const budgetPercent = Math.min(Math.round((project.spentCrore / project.budgetCrore) * 100), 100);

            return (
              <div
                key={project.id}
                className="group relative rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/90 dark:border-slate-800 shadow-sm hover:shadow-xl hover:border-orange-500/40 transition-all p-6 flex flex-col justify-between"
              >
                <div>
                  {/* Top Bar: Status & Risk Badges */}
                  <div className="flex items-center justify-between gap-2 mb-4">
                    {/* Status badge: Under Analysis, Active, Planning */}
                    <span
                      className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${getStatusBadge(
                        project.status
                      )}`}
                    >
                      {t(project.status, project.statusUrdu)}
                    </span>

                    {/* Risk Badge: Medium, Low, High */}
                    <div
                      className={`inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-1 rounded-full border ${riskConfig.badge}`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${riskConfig.dot}`} />
                      <span>{t(project.risk, project.riskUrdu)} {t("Risk", "خطرہ")}</span>
                    </div>
                  </div>

                  {/* Project Name */}
                  <h3 className="text-lg font-bold text-navy-900 dark:text-white group-hover:text-orange-500 transition-colors leading-snug">
                    {t(project.name, project.nameUrdu)}
                  </h3>

                  {/* Location & Type info */}
                  <div className="space-y-1.5 mt-2 mb-5">
                    <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                      <MapPin className="w-3.5 h-3.5 text-orange-500 flex-shrink-0" />
                      <span className="truncate">{project.location}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <Building2 className="w-3.5 h-3.5 flex-shrink-0" />
                      <span className="truncate">
                        {t(project.type, project.typeUrdu)} • {project.floors} {t("Floors", "منزلیں")}
                      </span>
                    </div>
                  </div>

                  {/* Budget & Spend Metric Box */}
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-100 dark:border-slate-800/80 mb-5">
                    <div className="flex items-baseline justify-between mb-2">
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                          {t("Total Budget", "کل بجٹ")}
                        </span>
                        <span className="text-base font-black text-navy-900 dark:text-white">
                          PKR {project.budgetCrore.toFixed(1)} {t("Crore", "کروڑ")}
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                          {t("Spent", "خرچ ہوا")}
                        </span>
                        <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
                          PKR {project.spentCrore.toFixed(1)} {t("Cr", "کروڑ")} ({budgetPercent}%)
                        </span>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-orange-500 rounded-full transition-all duration-500"
                        style={{ width: `${budgetPercent}%` }}
                      />
                    </div>

                    {/* Compliance Mini Badge */}
                    <div className="mt-2.5 pt-2 border-t border-slate-200/50 dark:border-slate-800/60 flex items-center justify-between text-xs">
                      <span className="text-slate-500 dark:text-slate-400">
                        {t("PBC 2021 Compliance", "پی بی سی 2021 تعمیل")}
                      </span>
                      <span
                        className={cn(
                          "font-bold text-xs",
                          project.complianceScore >= 90
                            ? "text-emerald-600 dark:text-emerald-400"
                            : project.complianceScore >= 75
                            ? "text-amber-600 dark:text-amber-400"
                            : "text-red-600 dark:text-red-400"
                        )}
                      >
                        {project.complianceScore}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Card Footer: Actions requested by User (Open Project, View Report) */}
                <div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mb-3">
                    <div className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{t(project.lastUpdate, project.lastUpdateUrdu)}</span>
                    </div>
                    <span>{project.engineer}</span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                    {/* Action 1: Open Project */}
                    <Link
                      href={`/dashboard/projects/${project.id}`}
                      className="py-2.5 px-3 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs text-center transition-all shadow-sm shadow-orange-500/20 flex items-center justify-center gap-1.5"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>{t("Open Project", "پروجیکٹ کھولیں")}</span>
                    </Link>

                    {/* Action 2: View Report */}
                    <Link
                      href={`/dashboard/reports?project=${project.id}`}
                      className="py-2.5 px-3 rounded-xl bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-navy-900 dark:text-white font-semibold text-xs text-center border border-slate-200 dark:border-slate-700 transition-all flex items-center justify-center gap-1.5"
                    >
                      <FileText className="w-3.5 h-3.5 text-orange-500" />
                      <span>{t("View Report", "رپورٹ دیکھیں")}</span>
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* TABLE VIEW (Autodesk Construction Cloud style) */
        <div className="overflow-x-auto rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-navy-950/60 text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">
                <th className="py-3.5 px-4">{t("Project Name", "منصوبے کا نام")}</th>
                <th className="py-3.5 px-4">{t("Location", "مقام")}</th>
                <th className="py-3.5 px-4">{t("Budget", "بجٹ")}</th>
                <th className="py-3.5 px-4">{t("Status", "حیثیت")}</th>
                <th className="py-3.5 px-4">{t("Risk Level", "رسک لیول")}</th>
                <th className="py-3.5 px-4">{t("Compliance", "تعمیل")}</th>
                <th className="py-3.5 px-4">{t("Last Update", "حالیہ اپ ڈیٹ")}</th>
                <th className="py-3.5 px-4 text-right">{t("Actions", "اقدامات")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-navy-900 dark:text-white font-medium">
              {filteredProjects.map((project) => {
                const riskConfig = getRiskBadge(project.risk);
                return (
                  <tr
                    key={project.id}
                    className="hover:bg-slate-50/80 dark:hover:bg-navy-800/40 transition-colors"
                  >
                    <td className="py-3.5 px-4">
                      <div className="font-bold text-sm text-navy-900 dark:text-white">
                        {t(project.name, project.nameUrdu)}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">{project.id}</div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-600 dark:text-slate-300">
                      {project.location}
                    </td>
                    <td className="py-3.5 px-4 font-bold">
                      PKR {project.budgetCrore.toFixed(1)} {t("Crore", "کروڑ")}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getStatusBadge(
                          project.status
                        )}`}
                      >
                        {t(project.status, project.statusUrdu)}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full border ${riskConfig.badge}`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${riskConfig.dot}`} />
                        {t(project.risk, project.riskUrdu)}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-bold">
                      <span
                        className={
                          project.complianceScore >= 90
                            ? "text-emerald-600"
                            : project.complianceScore >= 75
                            ? "text-amber-600"
                            : "text-red-600"
                        }
                      >
                        {project.complianceScore}%
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                      {t(project.lastUpdate, project.lastUpdateUrdu)}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Link
                          href={`/dashboard/projects/${project.id}`}
                          className="px-2.5 py-1.5 rounded-lg bg-orange-500 hover:bg-orange-600 text-white font-bold text-[11px] transition-colors"
                        >
                          {t("Open", "کھولیں")}
                        </Link>
                        <Link
                          href={`/dashboard/reports?project=${project.id}`}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-semibold text-[11px] border border-slate-200 dark:border-slate-700 transition-colors"
                        >
                          {t("Report", "رپورٹ")}
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ========================================================= */}
      {/* 5. MODAL: CREATE NEW PROJECT                              */}
      {/* ========================================================= */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/70 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-lg rounded-3xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6 sm:p-8">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-5 right-5 p-1.5 rounded-xl text-slate-400 hover:text-navy-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-orange-500/10 text-orange-500 flex items-center justify-center">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-navy-900 dark:text-white">
                  {t("Create New Construction Project", "نیا تعمیراتی پروجیکٹ بنائیں")}
                </h3>
                <p className="text-xs text-slate-400">
                  {t("Set up project boundaries, municipal authority, and budget.", "پروجیکٹ کی معلومات اور بجٹ درج کریں۔")}
                </p>
              </div>
            </div>

            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                  {t("Project Name", "منصوبے کا نام")} *
                </label>
                <input
                  type="text"
                  required
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder={t("e.g. DHA Commercial Plaza", "مثال: ڈی ایچ اے کمرشل پلازہ")}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                    {t("City", "شہر")} *
                  </label>
                  <select
                    value={newProjectCity}
                    onChange={(e) => setNewProjectCity(e.target.value as any)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20"
                  >
                    <option value="Lahore">Lahore (LDA)</option>
                    <option value="Karachi">Karachi (SBCA)</option>
                    <option value="Islamabad">Islamabad (CDA)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                    {t("Budget (Crore)", "بجٹ (کروڑ)")} *
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      step="0.5"
                      required
                      value={newProjectBudgetCrore}
                      onChange={(e) => setNewProjectBudgetCrore(e.target.value)}
                      placeholder="12"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
                      {t("Crore", "کروڑ")}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                  {t("Site Address / Sector", "سائٹ کا پتہ / سیکٹر")}
                </label>
                <input
                  type="text"
                  value={newProjectLocation}
                  onChange={(e) => setNewProjectLocation(e.target.value)}
                  placeholder={t("e.g. Phase 6, Sector G", "مثال: فیز 6، سیکٹر جی")}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                  {t("Project Structure Type", "تعمیراتی قسم")}
                </label>
                <input
                  type="text"
                  value={newProjectType}
                  onChange={(e) => setNewProjectType(e.target.value)}
                  placeholder={t("e.g. Commercial G+12 Plaza", "مثال: کمرشل G+12 پلازہ")}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20"
                />
              </div>

              {/* Upload Dropzone Preview */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                  {t("Attach Architectural Drawing (Optional)", "نقشہ منسلک کریں (اختیاری)")}
                </label>
                <div className="border border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-4 text-center bg-slate-50 dark:bg-navy-950/40 cursor-pointer hover:border-orange-500 transition-colors">
                  <UploadCloud className="w-5 h-5 text-orange-500 mx-auto mb-1" />
                  <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">
                    {t("Drop CAD .dwg or blueprint PDF here", "سی اے ڈی ڈرائنگ یا پی ڈی ایف یہاں ڈراپ کریں")}
                  </span>
                </div>
              </div>

              <div className="pt-2 flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 py-2.5 rounded-xl font-bold text-xs bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
                >
                  {t("Cancel", "منسوخ کریں")}
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider text-white bg-orange-500 hover:bg-orange-600 shadow-md shadow-orange-500/20 transition-all flex items-center justify-center gap-1.5"
                >
                  <Plus className="w-4 h-4 stroke-[3]" />
                  <span>{t("Create Project", "پروجیکٹ بنائیں")}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
