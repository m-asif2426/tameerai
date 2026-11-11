"use client";

import { useState, useMemo, useEffect } from "react";
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
  FolderOpen,
  RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils";

import { Project, ProjectCity, ProjectStatus, ProjectRisk } from "@/types";
import { projectService } from "@/services/projectService";

export default function ProjectsPage() {
  const { t } = useLanguage();

  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [riskFilter, setRiskFilter] = useState<string>("all");
  const [cityFilter, setCityFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"recent" | "budgetDesc" | "budgetAsc" | "risk" | "name">("recent");
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");

  // Create Project Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectLocation, setNewProjectLocation] = useState("");
  const [newProjectCity, setNewProjectCity] = useState<"Lahore" | "Karachi" | "Islamabad">("Lahore");
  const [newProjectBudgetCrore, setNewProjectBudgetCrore] = useState("10");
  const [newProjectType, setNewProjectType] = useState("Commercial G+8");

  // Load genuine projects from backend on mount
  const loadProjects = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const items = await projectService.getProjects();
      setProjects(items);
    } catch (err: unknown) {
      console.error("[ProjectsPage] Failed to fetch projects:", err);
      setErrorMessage("Failed to load projects from server.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  // Filtering & Sorting logic
  const filteredProjects = useMemo(() => {
    return projects
      .filter((p) => {
        const matchesSearch =
          p.name.toLowerCase().includes(search.toLowerCase()) ||
          p.location.toLowerCase().includes(search.toLowerCase()) ||
          (p.engineer && p.engineer.toLowerCase().includes(search.toLowerCase())) ||
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
          const riskWeight: Record<string, number> = { High: 3, Medium: 2, Low: 1 };
          return (riskWeight[b.risk] || 0) - (riskWeight[a.risk] || 0);
        }
        return 0; // Default recent
      });
  }, [projects, search, statusFilter, riskFilter, cityFilter, sortBy]);

  // Handle New Project submission to PostgreSQL 17 backend
  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;

    setSubmitting(true);
    setErrorMessage(null);
    try {
      const created = await projectService.createProject({
        name: newProjectName.trim(),
        location: newProjectLocation.trim() || "Main Boulevard",
        city: newProjectCity,
        type: newProjectType,
        budgetCrore: parseFloat(newProjectBudgetCrore) || 10,
        floors: 6,
        areaSqft: "25,000 sq ft",
      });

      setProjects((prev) => [created, ...prev]);
      setIsModalOpen(false);
      setNewProjectName("");
      setNewProjectLocation("");
    } catch (err: unknown) {
      console.error("[ProjectsPage] Create project error:", err);
      setErrorMessage(
        err instanceof Error ? err.message : "Failed to create project in database."
      );
    } finally {
      setSubmitting(false);
    }
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
      default:
        return "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700";
    }
  };

  const getRiskBadge = (risk: Project["risk"]) => {
    switch (risk) {
      case "Low":
        return {
          badge: "bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800",
          dot: "bg-emerald-500",
        };
      case "Medium":
        return {
          badge: "bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800",
          dot: "bg-amber-500",
        };
      case "High":
        return {
          badge: "bg-red-50 dark:bg-red-950/50 text-red-700 dark:text-red-400 border-red-200 dark:border-red-800",
          dot: "bg-red-500 animate-pulse",
        };
      default:
        return {
          badge: "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700",
          dot: "bg-slate-400",
        };
    }
  };

  // Dynamic KPI calculations from verified DB projects
  const totalProjectsCount = projects.length;
  const underAnalysisCount = projects.filter((p) => p.status === "Under Analysis").length;
  const highRiskCount = projects.filter((p) => p.risk === "High").length;
  const avgCompliance =
    totalProjectsCount > 0
      ? (
          projects.reduce((acc, p) => acc + (p.complianceScore || 100), 0) /
          totalProjectsCount
        ).toFixed(1) + "%"
      : "100%";

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans">
      {/* ========================================================= */}
      {/* 1. TOP HEADER & PRIMARY ACTION                            */}
      {/* ========================================================= */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <h1 className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white tracking-tight flex items-center gap-2.5">
            <Building2 className="w-6 h-6 text-orange-500" />
            <span>{t("Project Portfolio", "منصوبوں کی فہرست (Project Portfolio)")}</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t(
              "Centralized construction project workspaces with persistent PostgreSQL 17 tracking, building bylaw verification, and live BOQ intelligence.",
              "تمام زیرِ تعمیر اور مجوزہ منصوبوں کی نگرانی، خودکار ضوابط جانچ اور لاگت کا انتظام۔"
            )}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={loadProjects}
            className="p-2 rounded-xl text-slate-500 hover:text-navy-900 dark:hover:text-white bg-slate-100 dark:bg-navy-900 border border-slate-200 dark:border-slate-800 transition-colors shadow-2xs"
            title={t("Refresh projects", "منصوبے ریفریش کریں")}
            aria-label="Refresh projects"
          >
            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin text-orange-500")} />
          </button>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs uppercase tracking-wider shadow-md shadow-orange-500/20 transition-all active:scale-95"
          >
            <Plus className="w-4 h-4" />
            <span>{t("New Project", "نیا منصوبہ")}</span>
          </button>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 2. STATS ROW (Dynamic from genuine DB records)            */}
      {/* ========================================================= */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {t("Total Projects", "کل منصوبے")}
          </p>
          <p className="text-xl sm:text-2xl font-black text-navy-900 dark:text-white mt-1">
            {totalProjectsCount}
          </p>
          <span className="text-[10px] text-slate-500 dark:text-slate-400">
            {t("PostgreSQL 17 Persisted", "ڈیٹا بیس میں محفوظ")}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {t("Under Analysis", "زیرِ تجزیہ")}
          </p>
          <p className="text-xl sm:text-2xl font-black text-amber-600 dark:text-amber-400 mt-1">
            {underAnalysisCount} {t("Workspaces", "ورک اسپیس")}
          </p>
          <span className="text-[10px] text-slate-500 dark:text-slate-400">
            {t("Active Audits Running", "فعال آڈٹ جاری")}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {t("Average Compliance", "اوسط تعمیل اسکور")}
          </p>
          <p className="text-xl sm:text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1">
            {avgCompliance}
          </p>
          <span className="text-[10px] text-slate-500 dark:text-slate-400">
            {t("PBC 2021 Benchmark", "پی بی سی 2021 معیار")}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {t("High Risk Alerts", "ہائی رسک الرٹس")}
          </p>
          <p className="text-xl sm:text-2xl font-black text-red-600 dark:text-red-400 mt-1">
            {highRiskCount} {t("Flagged", "نشان زد")}
          </p>
          <span className="text-[10px] text-red-600 dark:text-red-400 font-semibold">
            {t("Engineering Review Required", "انجینئرنگ جائزہ درکار")}
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
              "Search by project name, location, or ID...",
              "منصوبے کا نام، مقام یا آئی ڈی تلاش کریں..."
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
              <option value="Lahore">Lahore (LDA)</option>
              <option value="Karachi">Karachi (SBCA)</option>
              <option value="Islamabad">Islamabad (CDA)</option>
            </select>
          </div>

          {/* Sort By */}
          <div className="flex items-center gap-1.5 bg-slate-100/70 dark:bg-navy-950 px-2.5 py-1.5 rounded-xl border border-slate-200/60 dark:border-slate-800">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-transparent text-xs font-semibold text-slate-700 dark:text-slate-300 focus:outline-none cursor-pointer"
            >
              <option value="recent">{t("Recently Updated", "حالیہ اپ ڈیٹس")}</option>
              <option value="budgetDesc">{t("Budget: High to Low", "بجٹ: زیادہ سے کم")}</option>
              <option value="budgetAsc">{t("Budget: Low to High", "بجٹ: کم سے زیادہ")}</option>
              <option value="risk">{t("Risk Priority", "خطرہ کے لحاظ سے")}</option>
              <option value="name">{t("Project Name (A-Z)", "نام کے لحاظ سے")}</option>
            </select>
          </div>

          {/* View Mode Toggle: Grid / Table */}
          <div className="flex items-center gap-1 bg-slate-100/70 dark:bg-navy-950 p-1 rounded-xl border border-slate-200/60 dark:border-slate-800">
            <button
              onClick={() => setViewMode("grid")}
              className={cn(
                "p-1.5 rounded-lg transition-colors",
                viewMode === "grid"
                  ? "bg-white dark:bg-navy-800 text-orange-500 shadow-2xs"
                  : "text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
              )}
              title={t("Grid View", "گرڈ ویو")}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode("table")}
              className={cn(
                "p-1.5 rounded-lg transition-colors",
                viewMode === "table"
                  ? "bg-white dark:bg-navy-800 text-orange-500 shadow-2xs"
                  : "text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
              )}
              title={t("Table View", "ٹیبل ویو")}
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Loading Skeleton */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 animate-pulse h-64"
            >
              <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-24 mb-3" />
              <div className="h-6 bg-slate-200 dark:bg-slate-800 rounded w-48 mb-2" />
              <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-36 mb-6" />
              <div className="h-10 bg-slate-200 dark:bg-slate-800 rounded w-full mt-auto" />
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && projects.length === 0 && (
        <div className="bg-white dark:bg-navy-900 rounded-3xl p-12 border border-slate-200/90 dark:border-slate-800 text-center max-w-xl mx-auto shadow-sm">
          <div className="w-16 h-16 rounded-2xl bg-orange-500/10 text-orange-500 flex items-center justify-center mx-auto mb-4 border border-orange-500/20">
            <FolderOpen className="w-8 h-8" />
          </div>
          <h2 className="text-lg font-bold text-navy-900 dark:text-white mb-2">
            {t("No Projects Created Yet", "ابھی تک کوئی منصوبہ شامل نہیں کیا گیا")}
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-6">
            {t(
              "Create your first construction project workspace to monitor building code compliance, track BOQ material rates, and run structural safety checks.",
              "اپنا پہلا تعمیراتی منصوبہ شامل کریں تاکہ پی بی سی 2021 ضوابط، ریٹ انٹیلی جنس اور سٹرکچرل سیفٹی کا تجزیہ شروع کیا جا سکے۔"
            )}
          </p>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs uppercase tracking-wider shadow-md shadow-orange-500/20 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>{t("Create First Project", "پہلا منصوبہ شامل کریں")}</span>
          </button>
        </div>
      )}

      {/* Filtered Empty State */}
      {!loading && projects.length > 0 && filteredProjects.length === 0 && (
        <div className="bg-white dark:bg-navy-900 rounded-2xl p-8 border border-slate-200 dark:border-slate-800 text-center text-xs text-slate-500">
          <p>{t("No projects match the selected filters or search terms.", "منتخب فلٹرز کے مطابق کوئی منصوبہ نہیں ملا۔")}</p>
          <button
            onClick={() => {
              setSearch("");
              setStatusFilter("all");
              setRiskFilter("all");
              setCityFilter("all");
            }}
            className="mt-3 text-orange-500 font-bold hover:underline"
          >
            {t("Reset all filters", "تمام فلٹرز ری سیٹ کریں")}
          </button>
        </div>
      )}

      {/* ========================================================= */}
      {/* 4. MAIN PROJECT LISTINGS                                   */}
      {/* ========================================================= */}
      {!loading && filteredProjects.length > 0 && viewMode === "grid" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredProjects.map((project) => {
            const riskInfo = getRiskBadge(project.risk);
            const statusClass = getStatusBadge(project.status);

            return (
              <div
                key={project.id}
                className="group relative bg-white dark:bg-navy-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 p-5 shadow-2xs hover:shadow-xl hover:border-orange-500/40 transition-all duration-300 flex flex-col justify-between"
              >
                <div>
                  {/* Top Bar: Code + Status Badge */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 dark:bg-navy-950 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800">
                      {project.id}
                    </span>
                    <span className={cn("text-[11px] font-bold px-2.5 py-0.5 rounded-full border", statusClass)}>
                      {t(project.status, project.statusUrdu)}
                    </span>
                  </div>

                  {/* Project Name */}
                  <h3 className="text-base font-bold text-navy-900 dark:text-white group-hover:text-orange-500 transition-colors line-clamp-1">
                    <Link href={`/dashboard/projects/${project.id}`}>
                      {t(project.name, project.nameUrdu)}
                    </Link>
                  </h3>

                  {/* Location & Authority */}
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-1">
                    <MapPin className="w-3.5 h-3.5 text-orange-500 flex-shrink-0" />
                    <span>{t(project.location, project.locationUrdu)}</span>
                  </div>

                  {/* Typology Badge */}
                  <div className="flex items-center gap-2 mt-3 text-xs">
                    <span className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-navy-950 text-slate-600 dark:text-slate-300 border border-slate-200/80 dark:border-slate-800 text-[11px] font-medium">
                      {t(project.type, project.typeUrdu)}
                    </span>
                    <span className="text-slate-400 text-[11px]">
                      {project.floors} {t("Floors", "منزلیں")}
                    </span>
                  </div>

                  {/* Budget & Spent Bar */}
                  <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-400">{t("Approved Budget", "منظور شدہ بجٹ")}</span>
                      <span className="font-black text-navy-900 dark:text-white font-mono">
                        PKR {project.budgetCrore.toFixed(1)} {t("Cr", "کروڑ")}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Card Footer: Compliance Score + View Button */}
                <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-bold text-xs">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>{project.complianceScore ?? 100}%</span>
                    </div>
                    <span className="text-slate-300 dark:text-slate-700">•</span>
                    <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded-full border inline-flex items-center gap-1", riskInfo.badge)}>
                      <span className={cn("w-1.5 h-1.5 rounded-full", riskInfo.dot)} />
                      <span>{t(project.risk, project.riskUrdu)}</span>
                    </span>
                  </div>

                  <Link
                    href={`/dashboard/projects/${project.id}`}
                    className="inline-flex items-center gap-1 text-xs font-bold text-orange-500 hover:text-orange-600 transition-colors"
                  >
                    <span>{t("Open Workspace", "ورک اسپیس کھولیں")}</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ========================================================= */}
      {/* 5. TABLE VIEW MODE                                        */}
      {/* ========================================================= */}
      {!loading && filteredProjects.length > 0 && viewMode === "table" && (
        <div className="bg-white dark:bg-navy-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-2xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-navy-950/60 border-b border-slate-200/80 dark:border-slate-800 text-[10px] font-black uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="py-3 px-4">{t("Code", "کوڈ")}</th>
                  <th className="py-3 px-4">{t("Project Name & Location", "نام اور مقام")}</th>
                  <th className="py-3 px-4">{t("City", "شہر")}</th>
                  <th className="py-3 px-4">{t("Typology", "نوعیت")}</th>
                  <th className="py-3 px-4">{t("Budget (PKR)", "بجٹ")}</th>
                  <th className="py-3 px-4">{t("Status", "حیثیت")}</th>
                  <th className="py-3 px-4">{t("Risk", "خطرہ")}</th>
                  <th className="py-3 px-4">{t("Compliance", "تعمیل")}</th>
                  <th className="py-3 px-4 text-right">{t("Action", "عمل")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
                {filteredProjects.map((p) => {
                  const riskInfo = getRiskBadge(p.risk);
                  const statusClass = getStatusBadge(p.status);

                  return (
                    <tr
                      key={p.id}
                      className="hover:bg-slate-50/50 dark:hover:bg-navy-800/40 transition-colors"
                    >
                      <td className="py-3.5 px-4 font-mono font-bold text-slate-500 dark:text-slate-400">
                        {p.id}
                      </td>
                      <td className="py-3.5 px-4">
                        <Link
                          href={`/dashboard/projects/${p.id}`}
                          className="font-bold text-navy-900 dark:text-white hover:text-orange-500 transition-colors block"
                        >
                          {t(p.name, p.nameUrdu)}
                        </Link>
                        <span className="text-[11px] text-slate-400">{t(p.location, p.locationUrdu)}</span>
                      </td>
                      <td className="py-3.5 px-4 font-semibold text-slate-700 dark:text-slate-300">
                        {p.city}
                      </td>
                      <td className="py-3.5 px-4 text-slate-600 dark:text-slate-400">
                        {t(p.type, p.typeUrdu)}
                      </td>
                      <td className="py-3.5 px-4 font-mono font-bold text-navy-900 dark:text-white">
                        PKR {p.budgetCrore.toFixed(1)} Cr
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded-full border", statusClass)}>
                          {t(p.status, p.statusUrdu)}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded-full border inline-flex items-center gap-1", riskInfo.badge)}>
                          <span className={cn("w-1.5 h-1.5 rounded-full", riskInfo.dot)} />
                          <span>{t(p.risk, p.riskUrdu)}</span>
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-bold text-emerald-600 dark:text-emerald-400">
                        {p.complianceScore ?? 100}%
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <Link
                          href={`/dashboard/projects/${p.id}`}
                          className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-orange-500/10 hover:bg-orange-500 text-orange-600 hover:text-white font-bold text-xs transition-colors"
                        >
                          <span>{t("Open", "کھولیں")}</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* 6. CREATE PROJECT MODAL                                   */}
      {/* ========================================================= */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/70 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-lg rounded-3xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 p-6 sm:p-8 shadow-2xl">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-5 right-5 p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              aria-label="Close modal"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-orange-500/10 text-orange-500 flex items-center justify-center border border-orange-500/20">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-navy-900 dark:text-white">
                  {t("Create New Construction Project", "نیا تعمیراتی منصوبہ شامل کریں")}
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {t("Persists to PostgreSQL 17 multi-tenant schema", "ڈیٹا بیس میں محفوظ ہوگا")}
                </p>
              </div>
            </div>

            {errorMessage && (
              <div className="mb-4 p-3 rounded-xl bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-400 text-xs">
                {errorMessage}
              </div>
            )}

            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  {t("Project Name", "منصوبے کا نام")} *
                </label>
                <input
                  type="text"
                  required
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="e.g. Gulberg Executive Tower"
                  className="w-full px-3.5 py-2.5 text-xs rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  {t("Site Address / Location", "سائیٹ کا پتہ / مقام")} *
                </label>
                <input
                  type="text"
                  required
                  value={newProjectLocation}
                  onChange={(e) => setNewProjectLocation(e.target.value)}
                  placeholder="e.g. Main Boulevard, Gulberg III"
                  className="w-full px-3.5 py-2.5 text-xs rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    {t("City Jurisdiction", "شہر اور اتھارٹی")}
                  </label>
                  <select
                    value={newProjectCity}
                    onChange={(e) => setNewProjectCity(e.target.value as any)}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
                  >
                    <option value="Lahore">Lahore (LDA)</option>
                    <option value="Karachi">Karachi (SBCA)</option>
                    <option value="Islamabad">Islamabad (CDA)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    {t("Budget (Crore PKR)", "بجٹ (کروڑ روپے)")}
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    value={newProjectBudgetCrore}
                    onChange={(e) => setNewProjectBudgetCrore(e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  {t("Typology", "عمارت کی قسم")}
                </label>
                <select
                  value={newProjectType}
                  onChange={(e) => setNewProjectType(e.target.value)}
                  className="w-full px-3.5 py-2.5 text-xs rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500"
                >
                  <option value="Commercial Plaza">Commercial Plaza (G+8)</option>
                  <option value="Residential Villa">Residential Villa (1-2 Kanal)</option>
                  <option value="Industrial Warehouse">Industrial Warehouse</option>
                  <option value="Mixed-Use High-Rise">Mixed-Use High-Rise (G+15)</option>
                  <option value="Educational / Institutional">Educational / Institutional</option>
                </select>
              </div>

              <div className="pt-4 flex items-center justify-end gap-2.5 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  disabled={submitting}
                  className="px-4 py-2.5 text-xs font-bold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
                >
                  {t("Cancel", "منسوخ")}
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white font-bold text-xs uppercase tracking-wider shadow-md shadow-orange-500/20 transition-all"
                >
                  {submitting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>{submitting ? t("Creating...", "تخلیق ہو رہا ہے...") : t("Create Project", "منصوبہ شامل کریں")}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
